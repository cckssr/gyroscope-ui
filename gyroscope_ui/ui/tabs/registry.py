"""Tab registry: later phases add tabs by registering a class, the main window stays untouched."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget

if TYPE_CHECKING:  # ``ui/context.py`` is added with the main window (Phase 4)
    from gyroscope_ui.ui.context import AppContext


class TabBase(QWidget):
    """Base class of central tabs.

    Subclasses set ``tab_id``, ``title_key`` (key below ``ui.`` in config.json) and ``order``
    and are decorated with ``@TabRegistry.register``.
    """

    tab_id: str = ""
    title_key: str = ""
    order: int = 100

    def __init__(self, context: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.context = context

    def on_activated(self) -> None:
        """The tab became the visible one."""

    def on_deactivated(self) -> None:
        """Another tab became visible."""


class TabRegistry:
    _tabs: list[type[TabBase]] = []

    @classmethod
    def register(cls, tab_class: type[TabBase]) -> type[TabBase]:
        if any(t.tab_id == tab_class.tab_id for t in cls._tabs):
            raise ValueError(f"duplicate tab id {tab_class.tab_id!r}")
        cls._tabs.append(tab_class)
        return tab_class

    @classmethod
    def tabs(cls) -> list[type[TabBase]]:
        return sorted(cls._tabs, key=lambda t: t.order)
