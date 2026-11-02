"""Application-wide keyboard shortcuts (see ``docs/SHORTCUTS.md``).

Why an application event filter instead of ``QShortcut``/``QAction``: line edits and spin boxes
claim many key combinations by accepting the ``ShortcutOverride`` event, so a ``QShortcut`` never
fires while one of them has the focus. The filter sees the event before the widget, accepts the
override for its own bindings and acts on the key press, so every binding works with any widget
focused. Exceptions: a plain key without modifiers (``Space``) is left to the focused widget when
that is a button (it clicks) or a text field (it types a space); ``Esc`` always acts.

Key presses are matched on ``event.key()`` and the modifiers (never on the text, which is
composed on macOS when Option is held); auto-repeat is ignored.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractSpinBox,
    QApplication,
    QLineEdit,
    QPlainTextEdit,
    QTextEdit,
    QWidget,
)

from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.infrastructure.logging import get_logger
from gyroscope_ui.ui.context import AppContext
from gyroscope_ui.ui.shortcuts import (
    Chord,
    chord_for_key,
    chord_from_event,
    chord_from_string,
    modifier_value,
)

_log = get_logger("shortcut_ctrl")
_K = Qt.Key


@dataclass(frozen=True)
class _Binding:
    chord: Chord
    action: str
    arg: Any = None


class ShortcutController(QObject):
    """Installs the application event filter and dispatches the bindings of the config.

    ``host`` is the main window: it provides ``select_tab``, ``save_measurement``,
    ``auto_range`` and ``toggle_shortcut_help``.
    """

    def __init__(
        self, config: AppConfig, context: AppContext, host: QWidget, parent: QObject | None = None
    ) -> None:
        super().__init__(parent if parent is not None else host)
        self._cfg = config
        self._ctx = context
        self._host = host
        self._installed = False
        self._bindings: dict[Chord, _Binding] = {}
        self._actions: dict[str, tuple[Callable[[Any], None], Callable[[], bool]]] = {}
        self._register_actions()
        self._build_bindings()

    # ---- life cycle ----------------------------------------------------------------------
    def install(self) -> None:
        app = QApplication.instance()
        if app is not None and not self._installed:
            app.installEventFilter(self)
            self._installed = True

    def uninstall(self) -> None:
        app = QApplication.instance()
        if app is not None and self._installed:
            app.removeEventFilter(self)
        self._installed = False

    # ---- bindings ------------------------------------------------------------------------
    def _register_actions(self) -> None:
        ctx = self._ctx
        host: Any = self._host
        m = ctx.measurement

        def always() -> bool:
            return True

        def can_toggle() -> bool:
            return m.is_recording or m.can_start

        self._actions = {
            "stop": (lambda _a: m.stop(), always),
            "start_stop": (lambda _a: m.toggle(), can_toggle),
            "reset": (lambda _a: m.reset(), lambda: m.state in ("stopped", "saved")),
            "save": (lambda _a: host.save_measurement(), lambda: m.can_save),
            "connect": (lambda _a: ctx.connection.toggle(), always),
            "auto_range": (lambda _a: host.auto_range(), always),
            "switch_tab": (lambda i: host.select_tab(i), always),
            "help": (lambda _a: host.toggle_shortcut_help(), always),
        }

    def _bind(self, text: str | None, action: str, arg: Any = None) -> None:
        chord = chord_from_string(text) if text else None
        if chord is None:
            if text:
                _log.warning("shortcut %r for %s is not a valid key sequence", text, action)
            return
        if chord in self._bindings:
            _log.warning("shortcut %r is bound twice (%s)", text, action)
            return
        self._bindings[chord] = _Binding(chord, action, arg)

    def _build_bindings(self) -> None:
        c = self._cfg.section("shortcuts")
        for action in ("stop", "start_stop", "reset", "save", "connect", "auto_range", "help"):
            self._bind(c.get(action), action)
        tab_mods = modifier_value(c.get("tab_modifier", "Ctrl"))
        for n in range(1, 10):
            chord = chord_for_key(_K(_K.Key_0.value + n)).with_mods(tab_mods)
            if chord in self._bindings:
                _log.warning("tab shortcut %d collides with another binding", n)
            else:
                self._bindings[chord] = _Binding(chord, "switch_tab", n - 1)

    def bound_chords(self) -> dict[Chord, str]:
        return {chord: b.action for chord, b in self._bindings.items()}

    # ---- event filter --------------------------------------------------------------------
    def _belongs_to_host(self, obj: QObject) -> bool:
        w = obj.window() if isinstance(obj, QWidget) else None
        while w is not None:
            if w is self._host:
                return True
            w = w.parentWidget()
        return False

    @staticmethod
    def _overlay_open() -> bool:
        """A popup (combo list, menu) or a modal dialog is open: only Esc still acts."""
        return QApplication.activePopupWidget() is not None or (
            QApplication.activeModalWidget() is not None
        )

    @staticmethod
    def _wants_plain_keys(widget: QWidget | None) -> bool:
        """``widget`` uses a plain key itself: buttons click on Space, text fields type."""
        if isinstance(widget, (QAbstractButton, QTextEdit, QPlainTextEdit)):
            return True
        if isinstance(widget, QLineEdit):
            return not isinstance(widget.parentWidget(), QAbstractSpinBox)
        return False

    def _focus_wants_plain_keys(self, receiver: QWidget) -> bool:
        """The receiver of the key event, or the focused widget, uses plain keys itself."""
        return self._wants_plain_keys(receiver) or self._wants_plain_keys(
            QApplication.focusWidget()
        )

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        etype = event.type()
        if etype not in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
            return False
        if not isinstance(obj, QWidget) or not self._belongs_to_host(obj):
            return False
        assert isinstance(event, QKeyEvent)
        chord = chord_from_event(event)
        binding = self._bindings.get(chord)
        if binding is None:
            return False
        action, guard = self._actions[binding.action]
        is_stop = binding.action == "stop"
        if not is_stop:
            if self._overlay_open() or not guard():
                return False
            if chord.mods == 0 and self._focus_wants_plain_keys(obj):
                return False
        elif not self._ctx.measurement.is_recording:
            return False  # Esc keeps its normal meaning (close a popup, cancel a dialog)
        if etype == QEvent.Type.ShortcutOverride:
            if is_stop and self._overlay_open():
                return False
            event.accept()
            return True
        if event.isAutoRepeat():
            return True
        try:
            action(binding.arg)
        except Exception:
            _log.exception("shortcut action %s failed", binding.action)
        return not (is_stop and self._overlay_open())
