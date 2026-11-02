"""Connect / disconnect, the simulation switch and the link state of the device.

States (``LinkState`` values): ``disconnected``, ``connecting``, ``connected``, ``stale``,
``lost``, ``error``. The controller owns the :class:`ConnectWorker` and, once the device is open,
the :class:`AcquisitionWorker`. It connects to the worker's signals once per worker and
re-emits them, so the other controllers connect to *this* object exactly once and a reconnect
can never duplicate a connection (D2). After an error a new attempt works without a restart.

Shutdown never destroys a running ``QThread``: a worker that does not end in time is kept in a
list of lingering workers, and the device is closed only after it has finished.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from concurrent.futures import Future
from typing import Any

from PySide6.QtCore import QObject, Signal

from gyroscope_ui.core.models import DeviceInfo, LinkState
from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.infrastructure.devices.base import GyroDevice
from gyroscope_ui.infrastructure.devices.discovery import create_device
from gyroscope_ui.infrastructure.logging import get_logger
from gyroscope_ui.infrastructure.qt_threads import AcquisitionWorker, ConnectWorker
from gyroscope_ui.ui.future_bridge import FutureBridge
from gyroscope_ui.ui.messages import error_text, message_text

_log = get_logger("connection")

_WORKER_WAIT_MS = 5_000  # join time of a worker on disconnect
_SHUTDOWN_WAIT_MS = 20_000  # extra wait for threads that ignored the first stop at exit
_ATTACHED = (LinkState.CONNECTING, LinkState.CONNECTED, LinkState.STALE, LinkState.LOST)

DeviceFactory = Callable[[AppConfig, bool], GyroDevice]


class ConnectionController(QObject):
    """Signals:
    state_changed(str, str): ``LinkState`` value and German status text
    device_changed(object): ``DeviceInfo`` of the open device, or None
    simulate_changed(bool): the simulation switch changed
    samples_ready(object): ``SampleBatch`` from the acquisition worker (GUI thread)
    stats_ready(object): ``LinkStats`` from the acquisition worker (GUI thread)
    message(str, str): level and text for the status bar
    """

    state_changed = Signal(str, str)
    device_changed = Signal(object)
    simulate_changed = Signal(bool)
    samples_ready = Signal(object)
    stats_ready = Signal(object)
    message = Signal(str, str)

    def __init__(
        self,
        config: AppConfig,
        *,
        factory: DeviceFactory = create_device,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._cfg = config
        self._factory = factory
        self._state = LinkState.DISCONNECTED
        self._simulate = False
        self._device: GyroDevice | None = None
        self._info: DeviceInfo | None = None
        self._connect_worker: ConnectWorker | None = None
        self._worker: AcquisitionWorker | None = None
        self._was_connected = False  # data arrived since the last connect (for "reconnected")
        # threads that did not end in time -> device to close once they have
        self._lingering: dict[QObject, GyroDevice | None] = {}
        self._bridge = FutureBridge(self)

    # ---- state ---------------------------------------------------------------------------
    @property
    def state(self) -> str:
        return self._state.value

    @property
    def is_attached(self) -> bool:
        """An acquisition worker runs (connected, stale or lost, or waiting for first data)."""
        return self._worker is not None

    @property
    def has_data(self) -> bool:
        """Data are flowing (connected) or paused only briefly (stale)."""
        return self._state in (LinkState.CONNECTED, LinkState.STALE)

    @property
    def simulate(self) -> bool:
        return self._simulate

    @property
    def device_info(self) -> DeviceInfo | None:
        return self._info

    def set_simulate(self, on: bool) -> None:
        """Switch the simulation on / off (only while disconnected)."""
        on = bool(on)
        if self._state in _ATTACHED:
            self.message.emit("warning", message_text(self._cfg, "disconnect_first"))
            self.simulate_changed.emit(self._simulate)  # let the switches snap back
            return
        if on != self._simulate:
            self._simulate = on
            self.simulate_changed.emit(on)

    def _set_state(self, state: LinkState) -> None:
        self._state = state
        key = state.value
        if state is LinkState.CONNECTED and self._simulate:
            key = "connected_simulation"
        self.state_changed.emit(state.value, self._cfg.text(f"connection_panel.state_{key}"))

    def _set_info(self, info: DeviceInfo | None) -> None:
        self._info = info
        self.device_changed.emit(info)

    # ---- actions -------------------------------------------------------------------------
    def connect_device(self, simulate: bool | None = None) -> None:
        """Open the device (or the simulation) off the GUI thread, then start acquiring."""
        if self._state in _ATTACHED or self._connect_worker is not None:
            return
        if simulate is not None:
            self.set_simulate(simulate)
        self._set_state(LinkState.CONNECTING)
        try:
            device = self._factory(self._cfg, self._simulate)
        except Exception as exc:
            _log.exception("cannot create the device")
            self._fail(error_text(self._cfg, exc))
            return
        self._device = device
        worker = ConnectWorker(device, parent=self)
        worker.connected.connect(self._on_opened)
        worker.failed_error.connect(self._on_open_failed)
        self._connect_worker = worker
        worker.start()

    def disconnect_device(self) -> None:
        """Stop acquiring, close the device and forget it."""
        self._reap_connect_worker()
        self._detach_worker()
        self._close_device()
        self._set_info(None)
        self._was_connected = False
        self._set_state(LinkState.DISCONNECTED)

    def toggle(self) -> None:
        if self._state in (LinkState.DISCONNECTED, LinkState.ERROR):
            self.connect_device()
        else:
            self.disconnect_device()

    def run_device(self, fn: Callable[[GyroDevice], Any]) -> Future | None:
        """Run ``fn(device)`` on the acquisition thread; None without a device."""
        if self._worker is None:
            self.message.emit("warning", message_text(self._cfg, "device_not_open"))
            return None
        return self._worker.run_in_thread(fn)

    def watch(self, future: Future, callback: Callable[[Future], None]) -> None:
        """Call ``callback(future)`` on the GUI thread when ``future`` is done."""
        self._bridge.watch(future, callback)

    def shutdown(self) -> None:
        """Application exit: disconnect and wait for every thread that is still running."""
        if self._state is not LinkState.DISCONNECTED:
            self.disconnect_device()
        for thread in list(self._lingering):
            if thread.wait(_SHUTDOWN_WAIT_MS):  # type: ignore[attr-defined]
                self._release(thread)
            else:
                _log.error("a device thread is still running at exit")

    # ---- worker life cycle ---------------------------------------------------------------
    def _on_opened(self, device: GyroDevice) -> None:
        if device is not self._device:  # disconnected while opening
            return
        self._reap_connect_worker()
        c = self._cfg
        worker = AcquisitionWorker(
            device,
            batch_interval_s=float(c.get("acquisition.batch_interval_s", 0.05)),
            stats_interval_s=float(c.get("acquisition.stats_interval_s", 1.0)),
            keepalive_s=float(c.get("device.keepalive_s", 2.0)),
            data_timeout_s=float(c.get("device.data_timeout_s", 3.0)),
            lost_after_s=float(c.get("device.lost_after_s", 15.0)),
            parent=self,
        )
        worker.samples_ready.connect(self.samples_ready)
        worker.stats_ready.connect(self.stats_ready)
        worker.link_changed.connect(self._on_link)
        worker.command_failed.connect(self._on_command_failed)
        worker.failed.connect(self._on_worker_failed)
        self._worker = worker
        self._set_info(device.info)
        worker.start()

    def _on_open_failed(self, exc: BaseException) -> None:
        if self._connect_worker is None or self.sender() is not self._connect_worker:
            return  # disconnected while opening
        self._reap_connect_worker()
        self._close_device()
        self._fail(error_text(self._cfg, exc))

    def _fail(self, text: str) -> None:
        self._device = None
        self._set_info(None)
        self.message.emit("error", message_text(self._cfg, "connection_failed", error=text))
        self._set_state(LinkState.ERROR)

    def _on_link(self, value: str) -> None:
        if self._worker is None or self.sender() is not self._worker:
            return  # a late signal of a detached worker
        state = LinkState(value)
        previous = self._state
        if state is previous:
            return
        self._set_state(state)
        if state is LinkState.CONNECTED:
            device = self._info.device_id if self._info else "–"
            if self._was_connected and previous in (LinkState.STALE, LinkState.LOST):
                self.message.emit("info", message_text(self._cfg, "device_reconnected"))
            elif not self._was_connected:
                self.message.emit("info", message_text(self._cfg, "connected", device=device))
            self._was_connected = True
            if self._worker is not None and self._device is not None:
                self._set_info(self._device.info)  # the protocol version may be known now
        elif state is LinkState.STALE:
            self.message.emit("warning", message_text(self._cfg, "device_no_data"))
        elif state is LinkState.LOST:
            self.message.emit("error", message_text(self._cfg, "device_lost"))

    def _on_command_failed(self, key: str) -> None:
        self.message.emit("error", message_text(self._cfg, key))

    def _on_worker_failed(self, key: str) -> None:
        """The acquisition loop ended with an error: the device is lost."""
        if self._worker is None or self.sender() is not self._worker:
            return
        _log.error("acquisition failed: %s", key)
        self._detach_worker()
        self._close_device()
        self._set_info(None)
        self._was_connected = False
        self.message.emit("error", message_text(self._cfg, key))
        self._set_state(LinkState.ERROR)

    def _detach_worker(self) -> None:
        worker, self._worker = self._worker, None
        self._bridge.cancel_all()
        if worker is None:
            return
        for signal in (
            worker.samples_ready,
            worker.stats_ready,
            worker.link_changed,
            worker.command_failed,
            worker.failed,
        ):
            with contextlib.suppress(RuntimeError, TypeError):
                signal.disconnect()
        worker.abort()
        if worker.wait(_WORKER_WAIT_MS):
            worker.deleteLater()
        else:
            _log.error("the acquisition thread did not stop within %d ms", _WORKER_WAIT_MS)
            self._keep_until_finished(worker, self._device)
            self._device = None  # closed by _release once the thread has ended

    def _reap_connect_worker(self) -> None:
        """Join the connect worker; one that does not finish keeps the device until it does."""
        worker, self._connect_worker = self._connect_worker, None
        if worker is None:
            return
        if worker.wait(_WORKER_WAIT_MS):
            worker.deleteLater()
            return
        _log.error("the connect worker did not finish within %d ms", _WORKER_WAIT_MS)
        self._keep_until_finished(worker, self._device)
        self._device = None

    def _keep_until_finished(self, thread: QObject, device: GyroDevice | None) -> None:
        # Destroying a running QThread crashes: keep a strong reference until it ends.
        self._lingering[thread] = device
        thread.finished.connect(lambda: self._release(thread))  # type: ignore[attr-defined]

    def _release(self, thread: QObject) -> None:
        if thread not in self._lingering:
            return
        device = self._lingering.pop(thread)
        thread.deleteLater()
        if device is not None:
            self._close(device)

    def _close_device(self) -> None:
        device, self._device = self._device, None
        if device is not None:
            self._close(device)

    @staticmethod
    def _close(device: GyroDevice) -> None:
        try:
            device.close()
        except Exception as exc:
            _log.warning("error while closing the device: %s", exc)

    # ---- panel binding -------------------------------------------------------------------
    def bind_panel(self, panel: Any) -> None:
        panel.connect_requested.connect(lambda: self.connect_device())
        panel.disconnect_requested.connect(self.disconnect_device)
        panel.simulate_toggled.connect(self.set_simulate)
        self.state_changed.connect(panel.set_link)
        self.device_changed.connect(panel.set_device)
        self.simulate_changed.connect(panel.set_simulate)
        self.state_changed.connect(
            lambda state, _text: panel.set_simulate_enabled(state in ("disconnected", "error"))
        )
        panel.set_simulate(self._simulate)
        panel.set_device(self._info)
        self._set_state(self._state)
