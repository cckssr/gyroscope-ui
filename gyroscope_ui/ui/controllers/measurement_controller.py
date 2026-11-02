"""Start / Stop / Reset of a measurement, the recording, the live values and the preview.

States (CONCEPT 4.2): ``empty``, ``recording``, ``stopped`` (unsaved data), ``saved``.
Every ``SampleBatch`` of the connection goes into the rolling preview buffer; while recording it
also goes into the :class:`Recording`, which accepts only samples received after Start (D3) and
keeps the time base across device restarts (D4). A timer at ``display.rate_hz`` updates the live
panel and emits :attr:`refreshed`, on which the plots redraw; nothing redraws per batch.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal

from gyroscope_ui.core.models import LinkStats, SampleBatch
from gyroscope_ui.core.recording import Recording, RollingBuffer
from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.infrastructure.logging import get_logger
from gyroscope_ui.ui.controllers.connection_controller import ConnectionController
from gyroscope_ui.ui.messages import message_text

_log = get_logger("measurement")

EMPTY, RECORDING, STOPPED, SAVED = "empty", "recording", "stopped", "saved"


class MeasurementController(QObject):
    """Signals:
    state_changed(str): ``empty | recording | stopped | saved``
    stopped(): a recording ended (auto-save hooks in here)
    refreshed(): display tick; redraw from :attr:`recording` / :attr:`preview`
    message(str, str): level and text for the status bar

    ``confirm(text) -> bool`` asks the user before data are discarded (replaceable in tests).
    ``clock`` must be the clock of the samples' ``host_time_s`` (``time.monotonic``).
    """

    state_changed = Signal(str)
    stopped = Signal()
    refreshed = Signal()
    message = Signal(str, str)

    def __init__(
        self,
        config: AppConfig,
        connection: ConnectionController,
        *,
        clock: Callable[[], float] = time.monotonic,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._cfg = config
        self._connection = connection
        self._clock = clock
        self._state = EMPTY
        self.recording = Recording()
        rate_hz = float(config.get("simulation.rate_hz", 100))
        preview_s = float(config.get("display.preview_s", 30))
        self.preview = RollingBuffer(max(1, int(rate_hz * preview_s * 1.5)))
        self._limit_s = float(config.get("storage.recording_limit_s", 3600))
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self._invalid_at_start = 0
        self._invalid_now = 0
        self._interrupted = False
        self.confirm: Callable[[str], bool] = lambda _text: True
        self._panel: Any = None
        self._live: Any = None

        connection.samples_ready.connect(self._on_samples)
        connection.stats_ready.connect(self._on_stats)
        connection.state_changed.connect(self._on_link)

        self._timer = QTimer(self)
        rate = max(1.0, float(config.get("display.rate_hz", 10)))
        self._timer.setInterval(int(1000 / rate))
        self._timer.timeout.connect(self._refresh)
        self._timer.start()

    # ---- state ---------------------------------------------------------------------------
    @property
    def state(self) -> str:
        return self._state

    @property
    def is_recording(self) -> bool:
        return self._state == RECORDING

    @property
    def has_unsaved(self) -> bool:
        return self._state == STOPPED and len(self.recording) > 0

    @property
    def can_save(self) -> bool:
        return self._state in (STOPPED, SAVED) and len(self.recording) > 0

    @property
    def can_start(self) -> bool:
        return self._state != RECORDING and self._connection.has_data

    @property
    def invalid_lines(self) -> int:
        """Lines rejected by the link during the last recording."""
        return max(0, self._invalid_now - self._invalid_at_start)

    def _set_state(self, state: str) -> None:
        if state != self._state:
            self._state = state
            self.state_changed.emit(state)
        self._update_panel()

    # ---- actions -------------------------------------------------------------------------
    def start(self) -> bool:
        if self._state == RECORDING:
            return False
        if not self._connection.has_data:
            self.message.emit("warning", message_text(self._cfg, "start_needs_data"))
            return False
        if self.has_unsaved and not self.confirm(message_text(self._cfg, "unsaved_data")):
            return False
        self.recording.start(self._clock())
        self.start_time = datetime.now().astimezone()
        self.end_time = None
        self._invalid_at_start = self._invalid_now
        self._interrupted = False
        self._set_state(RECORDING)
        self.message.emit("info", message_text(self._cfg, "measurement_running"))
        return True

    def stop(self) -> bool:
        if self._state != RECORDING:
            return False
        self.recording.stop()
        self.end_time = datetime.now().astimezone()
        self._set_state(STOPPED)
        self.message.emit("info", message_text(self._cfg, "measurement_stopped"))
        self.stopped.emit()
        return True

    def toggle(self) -> None:
        if self._state == RECORDING:
            self.stop()
        else:
            self.start()

    def reset(self) -> bool:
        if self._state == RECORDING:
            return False
        if self.has_unsaved and not self.confirm(message_text(self._cfg, "reset_unsaved")):
            return False
        self.recording.reset()
        self.start_time = self.end_time = None
        self._set_state(EMPTY)
        self.message.emit("info", message_text(self._cfg, "data_reset"))
        self._refresh()
        return True

    def mark_saved(self) -> None:
        if self._state in (STOPPED, SAVED):
            self._set_state(SAVED)

    # ---- data ----------------------------------------------------------------------------
    def _on_samples(self, batch: SampleBatch) -> None:
        self.preview.extend(batch)
        if self._state == RECORDING:
            self.recording.append(batch)
            if self.recording.duration_s >= self._limit_s:
                self.stop()
                limit = int(self._limit_s)
                self.message.emit(
                    "warning", message_text(self._cfg, "recording_limit_reached", limit_s=limit)
                )

    def _on_stats(self, stats: LinkStats) -> None:
        self._invalid_now = stats.invalid

    def _on_link(self, state: str, _text: str) -> None:
        if state in ("disconnected", "error"):
            self._invalid_now = self._invalid_at_start = 0
            self.preview.clear()
        if self._state == RECORDING and state in ("lost", "error") and not self._interrupted:
            self._interrupted = True
            self.message.emit("warning", message_text(self._cfg, "recording_interrupted"))
        self._update_panel()

    def _refresh(self) -> None:
        if self._live is not None:
            latest = self.preview.latest() if self._connection.has_data else None
            if latest is None:
                self._live.show_values(None, None)
            else:
                self._live.show_values(latest["frequency_hz"], latest["gyro_z_rad_s"])
            self._live.show_recording(len(self.recording), self.recording.duration_s)
        self.refreshed.emit()

    # ---- panel binding -------------------------------------------------------------------
    def bind_panels(self, panel: Any, live: Any) -> None:
        self._panel, self._live = panel, live
        panel.start_stop_requested.connect(self.toggle)
        panel.reset_requested.connect(self.reset)
        self._update_panel()
        self._refresh()

    def _update_panel(self) -> None:
        if self._panel is None:
            return
        self._panel.set_state(self._state)
        self._panel.set_can_start(self.can_start)

    def shutdown(self) -> None:
        self._timer.stop()
        if self._state == RECORDING:
            self.stop()
