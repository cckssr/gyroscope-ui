"""Live values: rotation frequency, angular rate about z, recorded points and duration."""

from __future__ import annotations

import math

from PySide6.QtWidgets import QGroupBox, QLCDNumber, QWidget

from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.pyqt.live_panel_ui import Ui_LivePanel
from gyroscope_ui.ui.i18n import apply_strings


class LivePanel(QGroupBox):
    """View only: shows the numbers it is given."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_LivePanel()
        self.ui.setupUi(self)
        self._blank = "--"
        self._shown: dict[str, str] = {}
        self._lcds: dict[str, QLCDNumber] = {
            "frequency": self.ui.lcdFrequency,
            "gyro_z": self.ui.lcdGyroZ,
            "points": self.ui.lcdPoints,
        }

    def apply_config(self, config: AppConfig) -> None:
        apply_strings(self, config.section("ui").get("live_panel", {}))
        self._blank = config.text("live_panel.no_value")
        self.clear()

    @property
    def displayed(self) -> dict[str, str]:
        """The text of each number display (``frequency``, ``gyro_z``, ``points``)."""
        return dict(self._shown)

    def show_values(self, frequency_hz: float | None, gyro_z_rad_s: float | None) -> None:
        """Latest rotation frequency (2 decimals) and ω_z (3 decimals); ``None`` shows a dash."""
        self._show("frequency", frequency_hz, 2)
        self._show("gyro_z", gyro_z_rad_s, 3)

    def show_recording(self, points: int, duration_s: float) -> None:
        """Number of recorded points and the recording duration as ``mm:ss``."""
        self._set("points", str(int(points)))
        total = int(max(duration_s, 0.0))
        self.ui.labelDuration.setText(f"{total // 60:02d}:{total % 60:02d}")

    def clear(self) -> None:
        """Blank the live values and reset the recording counters."""
        self.show_values(None, None)
        self.show_recording(0, 0.0)

    def _show(self, key: str, value: float | None, decimals: int) -> None:
        if value is None or not math.isfinite(value):
            self._set(key, self._blank)
        else:
            self._set(key, f"{value:.{decimals}f}")

    def _set(self, key: str, text: str) -> None:
        self._shown[key] = text
        self._lcds[key].display(text)
