"""Apply the German UI strings from config.json to widgets built from Designer forms.

Keys are Designer object names (camelCase, no underscore; ``self`` is the root widget);
``name@kind`` selects another property: ``@tooltip``, ``@suffix``, ``@prefix``,
``@placeholder``, ``@title`` (window title).
Keys with an underscore (e.g. ``pixel_format``) are plain texts looked up by the code and are
skipped here.
"""

from __future__ import annotations

from PySide6.QtCore import QObject

from gyroscope_ui.infrastructure.logging import get_logger

_log = get_logger("i18n")


def apply_strings(root: QObject, strings: dict[str, str]) -> None:
    for key, text in strings.items():
        name, _, kind = key.partition("@")
        if "_" in name:
            continue
        obj: QObject | None = root if name == "self" else root.findChild(QObject, name)
        if obj is None:
            _log.warning("ui string for unknown object %r", name)
            continue
        if kind == "tooltip":
            obj.setToolTip(text)  # type: ignore[attr-defined]
        elif kind == "suffix":
            obj.setSuffix(text)  # type: ignore[attr-defined]
        elif kind == "prefix":
            obj.setPrefix(text)  # type: ignore[attr-defined]
        elif kind == "placeholder":
            obj.setPlaceholderText(text)  # type: ignore[attr-defined]
        elif kind == "title":
            obj.setWindowTitle(text)  # type: ignore[attr-defined]
        elif hasattr(obj, "setTitle"):
            obj.setTitle(text)
        elif hasattr(obj, "setText"):
            obj.setText(text)
        else:
            _log.warning("cannot set text on %r", name)
