"""Measurement panel: Start / Stop and Reset buttons and the measurement state text."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox, QWidget

from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.pyqt.measurement_panel_ui import Ui_MeasurementPanel
from gyroscope_ui.ui.i18n import apply_strings

STATES = ("empty", "recording", "stopped", "saved")


class MeasurementPanel(QGroupBox):
    """View only: emits user intents; the controller decides what they mean."""

    start_stop_requested = Signal()
    reset_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_MeasurementPanel()
        self.ui.setupUi(self)
        self._config: AppConfig | None = None
        self._state = "empty"
        self._can_start = False
        self.ui.buttonStartStop.clicked.connect(self.start_stop_requested)
        self.ui.buttonReset.clicked.connect(self.reset_requested)
        self._refresh()

    def apply_config(self, config: AppConfig) -> None:
        self._config = config
        apply_strings(self, config.section("ui").get("measurement_panel", {}))
        self._refresh()

    def set_state(self, state: str) -> None:
        """Show the measurement state: ``empty``, ``recording``, ``stopped`` or ``saved``."""
        if state not in STATES:
            raise ValueError(f"unknown measurement state {state!r}")
        self._state = state
        self._refresh()

    def set_can_start(self, enabled: bool) -> None:
        """Whether a measurement may be started now (the device delivers data)."""
        self._can_start = enabled
        self._refresh()

    def _refresh(self) -> None:
        recording = self._state == "recording"
        self.ui.buttonStartStop.setEnabled(recording or self._can_start)
        self.ui.buttonReset.setEnabled(self._state in ("stopped", "saved"))
        if self._config is not None:
            text = self._config.text
            self.ui.buttonStartStop.setText(
                text(
                    "measurement_panel.button_stop"
                    if recording
                    else "measurement_panel.button_start"
                )
            )
            self.ui.labelState.setText(text(f"measurement_panel.state_{self._state}"))
