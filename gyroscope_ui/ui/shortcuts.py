"""Keyboard shortcut definitions: parsing of the ``shortcuts`` config section, key matching,
display strings and the overview table (F1 dialog and ``docs/SHORTCUTS.md``).

Key sequences are Qt strings (``"Alt+Left"``). On macOS Qt maps ``Ctrl`` to the Command key
(⌘), ``Meta`` to Control (⌃); ``Alt`` is Option (⌥).

Matching works on ``event.key()`` plus the modifiers, never on ``event.text()``: Option+key
produces composed characters on macOS. Shifted symbol keys are folded onto their base key
(``+`` -> ``=``, ``_`` -> ``-``, ``{`` -> ``[``) so that ``Alt+Shift+=`` matches whatever the
keyboard layout reports for that physical key combination.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from PySide6.QtCore import QKeyCombination, Qt
from PySide6.QtGui import QKeyEvent, QKeySequence

from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.infrastructure.logging import get_logger

_log = get_logger("shortcuts")

_K = Qt.Key
_M = Qt.KeyboardModifier
_MOD_MASK = (
    _M.ControlModifier.value | _M.ShiftModifier.value | _M.AltModifier.value | _M.MetaModifier.value
)
# Shifted symbols are reported as their own key by some platforms / layouts.
_CANONICAL = {
    _K.Key_Plus.value: _K.Key_Equal.value,
    _K.Key_Underscore.value: _K.Key_Minus.value,
    _K.Key_BraceLeft.value: _K.Key_BracketLeft.value,
    _K.Key_BraceRight.value: _K.Key_BracketRight.value,
    _K.Key_Enter.value: _K.Key_Return.value,
    _K.Key_Backtab.value: _K.Key_Tab.value,
}
# macOS ANSI virtual key codes (kVK_*) of digits and letters: Option+key may arrive with a
# composed character instead of the key, the virtual key is the fallback.
_MAC_VK = {
    0x12: _K.Key_1, 0x13: _K.Key_2, 0x14: _K.Key_3, 0x15: _K.Key_4, 0x17: _K.Key_5,
    0x16: _K.Key_6, 0x1A: _K.Key_7, 0x1C: _K.Key_8, 0x19: _K.Key_9, 0x1D: _K.Key_0,
    0x00: _K.Key_A, 0x01: _K.Key_S, 0x02: _K.Key_D, 0x0E: _K.Key_E, 0x0F: _K.Key_R,
    0x28: _K.Key_K, 0x1F: _K.Key_O,
}  # fmt: skip
_MAC_SYMBOLS = {
    "Ctrl": "⌘",
    "Meta": "⌃",
    "Alt": "⌥",
    "Shift": "⇧",
    "Left": "←",
    "Right": "→",
    "Up": "↑",
    "Down": "↓",
    "Return": "↵",
    "Enter": "⌅",
    "Esc": "⎋",
    "Backspace": "⌫",
    "Del": "⌦",
    "Tab": "⇥",
    "Space": "␣",
}
_MAC_ORDER = ("Meta", "Alt", "Shift", "Ctrl")  # macOS convention: ⌃⌥⇧⌘
DOC_TABS = 1  # tabs of version 2.0 (CONCEPT section 8); the doc lists Ctrl+1 only


@dataclass(frozen=True)
class Chord:
    """One key with exact modifiers (no keypad / group-switch flags), keys canonicalised."""

    key: int
    mods: int

    def with_mods(self, extra: int) -> Chord:
        return Chord(self.key, self.mods | extra)


def canonical_key(key: int) -> int:
    return _CANONICAL.get(key, key)


def chord_from_string(text: str) -> Chord | None:
    """First key combination of a Qt key-sequence string, ``None`` if it cannot be parsed."""
    seq = QKeySequence(text, QKeySequence.SequenceFormat.PortableText)
    if seq.isEmpty() or seq[0].key() == _K.Key_unknown:
        return None
    combo = seq[0]
    return Chord(canonical_key(combo.key().value), combo.keyboardModifiers().value & _MOD_MASK)


def chord_for_key(key: Qt.Key, mods: int = 0) -> Chord:
    return Chord(canonical_key(key.value), mods)


def chord_from_event(event: QKeyEvent) -> Chord:
    """The chord of a key event: modifiers masked to Ctrl/Shift/Alt/Meta (macOS flags arrow
    keys as keypad keys), key canonicalised; Option+digit/letter via the virtual key."""
    key = event.key()
    mods = event.modifiers().value & _MOD_MASK
    if sys.platform == "darwin" and mods & _M.AltModifier.value:
        if key == 0 or 0x80 <= key < 0x01000000:  # composed character, not a Qt key
            mapped = _MAC_VK.get(event.nativeVirtualKey())
            if mapped is not None:
                key = mapped.value
    return Chord(canonical_key(key), mods)


def modifier_value(name: str) -> int:
    """``"Shift"`` / ``"Ctrl"`` / ``"Alt"`` / ``"Meta"`` (or a ``+`` combination) as flags."""
    value = 0
    for part in name.split("+"):
        flag = {
            "ctrl": _M.ControlModifier,
            "shift": _M.ShiftModifier,
            "alt": _M.AltModifier,
            "meta": _M.MetaModifier,
        }.get(part.strip().lower())
        if flag is not None:
            value |= flag.value
    return value


def modifier_key(mods: int) -> list[int]:
    """Key codes of the modifier keys contained in ``mods`` (for release tracking)."""
    out = []
    for flag, key in (
        (_M.ControlModifier, _K.Key_Control),
        (_M.ShiftModifier, _K.Key_Shift),
        (_M.AltModifier, _K.Key_Alt),
        (_M.MetaModifier, _K.Key_Meta),
    ):
        if mods & flag.value:
            out.append(key.value)
    return out


def sequence_string(chord: Chord) -> str:
    """Portable Qt string of a chord, e.g. ``"Alt+Shift+Left"``."""
    combo = QKeyCombination(_M(chord.mods), _K(chord.key))
    return QKeySequence(combo).toString(QKeySequence.SequenceFormat.PortableText)


def native_text(sequence: str) -> str:
    """Display text for the running platform (⌥← on macOS, ``Alt+Left`` elsewhere)."""
    return QKeySequence(sequence, QKeySequence.SequenceFormat.PortableText).toString(
        QKeySequence.SequenceFormat.NativeText
    )


def display_text(sequence: str, mac: bool) -> str:
    """Display text for a given platform family independent of the running one."""
    chord = chord_from_string(sequence)
    if chord is None:
        return sequence
    portable = sequence_string(chord)
    if not mac:
        return portable
    parts = portable.split("+")
    key = "+" if portable.endswith("++") else parts[-1]
    mods = [p for p in parts[:-1] if p]
    mods.sort(key=lambda m: _MAC_ORDER.index(m) if m in _MAC_ORDER else 99)
    return "".join(_MAC_SYMBOLS.get(m, m) for m in mods) + _MAC_SYMBOLS.get(key, key)


def key_hint(config: AppConfig, *ids: str) -> str:
    """`` (⌥←)`` style suffix for tooltips: the native text of the given config entries,
    joined with `` / `` (empty string if none is configured)."""
    cfg = config.section("shortcuts")
    texts = [native_text(cfg[i]) for i in ids if isinstance(cfg.get(i), str) and cfg[i]]
    return f" ({' / '.join(texts)})" if texts else ""


# ---- overview table -------------------------------------------------------------------------
@dataclass(frozen=True)
class ShortcutRow:
    """One line of the overview: ``keys`` are Qt sequence strings, shown joined with ``sep``."""

    id: str
    group: str
    keys: tuple[str, ...]
    sep: str = " / "

    def text(self, mac: bool) -> str:
        return self.sep.join(display_text(k, mac) for k in self.keys)

    def native(self) -> str:
        return self.sep.join(native_text(k) for k in self.keys)


def add_modifiers(sequence: str, extra: str) -> str:
    chord = chord_from_string(sequence)
    if chord is None:
        return sequence
    return sequence_string(chord.with_mods(modifier_value(extra)))


def with_digit(modifiers: str, digit: int) -> str:
    return sequence_string(Chord(_K.Key_0.value + digit, modifier_value(modifiers)))


def shortcut_rows(config: AppConfig, n_tabs: int = DOC_TABS) -> list[ShortcutRow]:
    """All shortcuts in display order, built from the ``shortcuts`` config section."""
    c = config.section("shortcuts")

    def seq(key: str) -> str | None:
        value = c.get(key)
        return value if isinstance(value, str) and chord_from_string(value) else None

    rows: list[ShortcutRow] = []

    def add(row_id: str, group: str, *keys: str | None, sep: str = " / ") -> None:
        present = tuple(k for k in keys if k)
        if present:
            rows.append(ShortcutRow(row_id, group, present, sep))

    tab_mod = c.get("tab_modifier", "Ctrl")
    add("start_stop", "measurement", seq("start_stop"))
    add("stop", "measurement", seq("stop"))
    add("reset", "measurement", seq("reset"))
    add("save", "files", seq("save"))
    add("connect", "device", seq("connect"))
    add("auto_range", "plot", seq("auto_range"))
    first, last = with_digit(tab_mod, 1), with_digit(tab_mod, max(n_tabs, 1))
    add("switch_tab", "window", *dict.fromkeys((first, last)), sep=" … ")
    add("help", "window", seq("help"))
    return rows


def render_markdown(config: AppConfig, n_tabs: int = DOC_TABS) -> str:
    """``docs/SHORTCUTS.md``: German table Funktion | macOS | Windows/Linux, generated from
    the config defaults (``python -m gyroscope_ui.ui.shortcuts > docs/SHORTCUTS.md``)."""
    ui = config.section("ui").get("shortcuts_dialog", {})
    labels, groups = ui.get("row_labels", {}), ui.get("group_names", {})
    md = config.section("ui").get("shortcuts_doc", {})
    lines = [f"# {md.get('title', 'Shortcuts')}", "", md.get("intro", ""), ""]
    columns = md["columns"]
    rows = shortcut_rows(config, n_tabs)
    for group in dict.fromkeys(r.group for r in rows):
        lines += [f"## {groups.get(group, group)}", ""]
        lines += [f"| {columns[0]} | {columns[1]} | {columns[2]} |", "| --- | --- | --- |"]
        for r in (r for r in rows if r.group == group):
            label = labels.get(r.id, r.id)
            lines.append(f"| {label} | {_cell(r.text(True))} | {_cell(r.text(False))} |")
        lines.append("")
    lines += [md.get("notes", ""), ""]
    return "\n".join(lines)


def _cell(text: str) -> str:
    return f"`{text}`"


if __name__ == "__main__":  # pragma: no cover
    from gyroscope_ui.infrastructure.config import load_config

    sys.stdout.write(render_markdown(load_config(), DOC_TABS))
