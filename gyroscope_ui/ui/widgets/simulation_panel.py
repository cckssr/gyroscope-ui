"""Simulation panel (shown by the main window only with the simulated device): start frequency
and the "Anwerfen" button."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox, QWidget

from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.pyqt.simulation_panel_ui import Ui_SimulationPanel
from gyroscope_ui.ui.i18n import apply_strings


class SimulationPanel(QGroupBox):
    kick_requested = Signal(float)  # start frequency in Hz

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_SimulationPanel()
        self.ui.setupUi(self)
        self.ui.buttonKick.clicked.connect(
            lambda: self.kick_requested.emit(self.ui.spinStartFrequency.value())
        )

    def apply_config(self, config: AppConfig) -> None:
        apply_strings(self, config.section("ui").get("simulation_panel", {}))
        spin = self.ui.spinStartFrequency
        start_hz = float(config.get("simulation.start_frequency_hz", spin.value()))
        spin.setValue(min(max(start_hz, spin.minimum()), spin.maximum()))
