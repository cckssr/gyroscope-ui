"""Qt worker threads. The only module in infrastructure/ that imports PySide6.

* ``ConnectWorker``: opens a device off the GUI thread.
* ``AcquisitionWorker``: owns the open device; reads, keeps it registered, tracks liveness and
  hands the samples to the GUI thread in batches (ARCHITECTURE section 3).
"""

from __future__ import annotations

import queue
import threading
import time
from collections.abc import Callable
from concurrent.futures import Future
from typing import Any, TypeVar

from PySide6.QtCore import QThread, Signal

from gyroscope_ui.core.models import LinkState, Sample, SampleBatch
from gyroscope_ui.infrastructure.devices.base import DeviceError, GyroDevice
from gyroscope_ui.infrastructure.logging import get_logger

_log = get_logger("threads")

T = TypeVar("T")

# QThread defaults to a 512 KiB stack on macOS; keep headroom for NumPy and logging.
_THREAD_STACK_BYTES = 16 * 1024 * 1024


class _WorkerThread(QThread):
    """QThread with a generous stack."""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.setStackSize(_THREAD_STACK_BYTES)


def _error_key(exc: BaseException, default: str) -> str:
    return exc.key if isinstance(exc, DeviceError) else default


class _CommandQueue:
    """Thread-safe queue of callables executed on the worker thread, with Future results."""

    def __init__(self) -> None:
        self._q: queue.SimpleQueue[tuple[Callable[[], Any], Future]] = queue.SimpleQueue()

    def submit(self, fn: Callable[[], Any]) -> Future:
        future: Future = Future()
        self._q.put((fn, future))
        return future

    def empty(self) -> bool:
        return self._q.empty()

    def run_pending(self) -> int:
        n = 0
        while True:
            try:
                fn, future = self._q.get_nowait()
            except queue.Empty:
                return n
            n += 1
            if not future.set_running_or_notify_cancel():
                continue
            try:
                future.set_result(fn())
            except BaseException as exc:
                future.set_exception(exc)

    def cancel_all(self) -> None:
        """Cancel everything still queued (worker ended or aborted)."""
        while True:
            try:
                _fn, future = self._q.get_nowait()
            except queue.Empty:
                return
            future.cancel()
            future.set_running_or_notify_cancel()


class AcquisitionWorker(_WorkerThread):
    """Owns the open device: one loop that reads, keeps alive, tracks liveness and batches.

    Thread-safe API: :meth:`run_in_thread`, :meth:`abort`. Call ``start()`` once; a reconnect
    uses a new worker. After ``start()`` only this thread touches the device.

    Loop (one pass): run queued commands, ``device.read(read_timeout_s)``, update the link
    state, keep-alive every ``keepalive_s``, emit the collected samples as one
    :class:`SampleBatch` at most every ``batch_interval_s``, emit the link statistics every
    ``stats_interval_s``. Link state: ``CONNECTING`` until the first valid sample, then
    ``CONNECTED``; no valid sample for ``data_timeout_s`` gives ``STALE``, for ``lost_after_s``
    ``LOST`` (measured from the start while nothing has arrived); data resumes ``CONNECTED``.

    Signals (delivered on the receiver's thread):
      samples_ready(SampleBatch): never empty
      link_changed(str): ``LinkState`` value, only on a change (first emission: ``connecting``)
      stats_ready(LinkStats): every ``stats_interval_s``
      command_failed(str): message key of a failed ``run_in_thread`` command (worker keeps going)
      failed(str): message key of a read failure or crash; the loop has ended
    """

    samples_ready = Signal(object)
    link_changed = Signal(str)
    stats_ready = Signal(object)
    command_failed = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        device: GyroDevice,
        *,
        batch_interval_s: float = 0.05,
        stats_interval_s: float = 1.0,
        keepalive_s: float = 2.0,
        data_timeout_s: float = 3.0,
        lost_after_s: float = 15.0,
        read_timeout_s: float = 0.05,
        clock: Callable[[], float] = time.monotonic,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._device = device
        self._batch_interval_s = batch_interval_s
        self._stats_interval_s = stats_interval_s
        self._keepalive_s = keepalive_s
        self._data_timeout_s = data_timeout_s
        self._lost_after_s = lost_after_s
        self._read_timeout_s = read_timeout_s
        self._clock = clock
        self._abort_event = threading.Event()
        self._ended = threading.Event()
        self._commands = _CommandQueue()
        self._state: LinkState | None = None

    # ---- thread-safe API ----------------------------------------------------------------
    def run_in_thread(self, fn: Callable[[GyroDevice], T]) -> Future:
        """Run ``fn(device)`` on the worker thread between two reads.

        The Future carries the result or the exception (which also emits ``command_failed``);
        it is cancelled if the worker is aborted or has ended.
        """
        future = self._commands.submit(self._guard(lambda: fn(self._device)))
        if self._abort_event.is_set() or self._ended.is_set():
            self._commands.cancel_all()
        return future

    def abort(self) -> None:
        """End the loop (noticed within one read timeout) and cancel pending commands."""
        self._abort_event.set()
        self._commands.cancel_all()

    # ---- internals ----------------------------------------------------------------------
    def _guard(self, fn: Callable[[], T]) -> Callable[[], T]:
        def _guarded() -> T:
            try:
                return fn()
            except Exception as exc:
                _log.error("command failed: %s", exc)
                self.command_failed.emit(_error_key(exc, "device_io_failed"))
                raise

        return _guarded

    def _set_state(self, state: LinkState) -> None:
        if state is not self._state:
            self._state = state
            self.link_changed.emit(state.value)

    def _update_link(self, got_samples: bool, now: float, last_valid_s: float) -> None:
        if got_samples:
            self._set_state(LinkState.CONNECTED)
            return
        silent_s = now - last_valid_s
        if silent_s >= self._lost_after_s:
            self._set_state(LinkState.LOST)
        elif silent_s >= self._data_timeout_s:
            self._set_state(LinkState.STALE)

    def _loop(self) -> None:
        device, clock = self._device, self._clock
        start_s = clock()
        last_valid_s = start_s
        next_keepalive_s = start_s + self._keepalive_s
        next_batch_s = start_s + self._batch_interval_s
        next_stats_s = start_s + self._stats_interval_s
        pending: list[Sample] = []
        self._set_state(LinkState.CONNECTING)
        while not self._abort_event.is_set():
            self._commands.run_pending()
            if self._abort_event.is_set():
                break
            samples = device.read(self._read_timeout_s)
            now = clock()
            if samples:
                pending.extend(samples)
                last_valid_s = now
            self._update_link(bool(samples), now, last_valid_s)
            if now >= next_keepalive_s:
                device.keepalive()
                next_keepalive_s = now + self._keepalive_s
            if pending and now >= next_batch_s:
                self.samples_ready.emit(SampleBatch.from_samples(pending))
                pending = []
                next_batch_s = now + self._batch_interval_s
            if now >= next_stats_s:
                self.stats_ready.emit(device.stats())
                next_stats_s = now + self._stats_interval_s

    # ---- thread body --------------------------------------------------------------------
    def run(self) -> None:
        try:
            self._loop()
        except DeviceError as exc:
            _log.error("device failed: %s", exc)
            self.failed.emit(exc.key)
        except Exception:
            _log.exception("acquisition worker crashed")
            self.failed.emit("device_io_failed")
        finally:
            self._ended.set()
            self._commands.cancel_all()


class ConnectWorker(_WorkerThread):
    """Opens a device off the GUI thread.

    Signals: connected(device) after a successful ``open()``; otherwise failed(str message key)
    and failed_error(exception) (the exception carries ``key`` and the format arguments of the
    message, e.g. the port of ``device_port_in_use``).
    """

    connected = Signal(object)
    failed = Signal(str)
    failed_error = Signal(object)

    def __init__(self, device: GyroDevice, parent: Any = None) -> None:
        super().__init__(parent)
        self._device = device

    def run(self) -> None:
        try:
            self._device.open()
        except Exception as exc:
            _log.error("cannot open the device: %s", exc)
            self.failed_error.emit(exc)
            self.failed.emit(_error_key(exc, "device_open_failed"))
        else:
            self.connected.emit(self._device)
