"""Small round status indicator."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

_COLORS = {
    "off": QColor(150, 150, 150),
    "ok": QColor(40, 180, 70),
    "busy": QColor(235, 170, 30),
    "warning": QColor(235, 170, 30),
    "error": QColor(210, 50, 50),
}


class StatusLed(QWidget):
    """LED with states ``off`` (grey), ``ok`` (green), ``busy`` / ``warning`` (amber), ``error``."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state = "off"
        self.setFixedSize(16, 16)

    @property
    def state(self) -> str:
        return self._state

    def set_state(self, state: str) -> None:
        if state not in _COLORS:
            raise ValueError(f"unknown LED state {state!r}")
        self._state = state
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(16, 16)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = _COLORS[self._state]
        painter.setBrush(color)
        painter.setPen(color.darker(150))
        painter.drawEllipse(2, 2, 12, 12)
