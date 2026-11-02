"""Single-line label that elides long text (file paths) in the middle."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import QLabel, QWidget


class ElidedLabel(QLabel):
    """Shows ``text`` on one line, cut out in the middle (``…``) when it does not fit; the full
    text is the tooltip. Never forces the layout wider (minimum width is small)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def setText(self, text: str) -> None:  # noqa: N802
        super().setText(text)
        self.setToolTip(text)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(40, super().minimumSizeHint().height())

    def elided_text(self) -> str:
        """The text as currently drawn."""
        return self.fontMetrics().elidedText(
            self.text(), Qt.TextElideMode.ElideMiddle, max(self.contentsRect().width(), 1)
        )

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.drawText(
            self.contentsRect(),
            int(self.alignment() | Qt.AlignmentFlag.AlignVCenter),
            self.elided_text(),
        )
