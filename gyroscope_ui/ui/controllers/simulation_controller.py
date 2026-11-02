"""Simulation-only commands of the mock device (the "Simulation" panel)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject

from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.ui.controllers.connection_controller import ConnectionController


class SimulationController(QObject):
    """Kicks the simulated disc; the panel is visible only while the simulation is selected."""

    def __init__(
        self, config: AppConfig, connection: ConnectionController, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._cfg = config
        self._connection = connection

    def kick(self, frequency_hz: float) -> None:
        """Spin the simulated disc up to ``frequency_hz`` (only connected to the simulation)."""
        if not self._connection.simulate or not self._connection.is_attached:
            return
        future = self._connection.run_device(lambda device: device.kick(frequency_hz))
        if future is not None:
            self._connection.watch(future, lambda f: f.exception())  # errors are logged

    def bind_panel(self, panel: Any) -> None:
        panel.kick_requested.connect(self.kick)
        self._connection.simulate_changed.connect(panel.setVisible)
        panel.setVisible(self._connection.simulate)
