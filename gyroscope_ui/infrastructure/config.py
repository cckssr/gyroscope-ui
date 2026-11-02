"""Application configuration: tunables and all (German) user-visible strings from config.json."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from gyroscope_ui.infrastructure.logging import get_logger

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
_log = get_logger("config")


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def _safe_format(text: str, fmt: dict[str, Any]) -> str:
    """``text.format(**fmt)``; a missing argument or a bad format spec returns ``text`` as is."""
    if not fmt:
        return text
    try:
        return text.format(**fmt)
    except (KeyError, IndexError, ValueError, TypeError, AttributeError):
        return text


class AppConfig:
    """Read-only view on the parsed config.json with dotted-path access."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def data(self) -> dict[str, Any]:
        return self._data

    def get(self, path: str, default: Any = None) -> Any:
        """Look up ``"section.key.subkey"``; ``default`` if any part is missing."""
        node: Any = self._data
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def section(self, name: str) -> dict[str, Any]:
        value = self._data.get(name, {})
        return value if isinstance(value, dict) else {}

    def text(self, path: str, **fmt: Any) -> str:
        """German UI string at ``ui.<path>``; falls back to the path itself (visible, not fatal)."""
        value = self.get(f"ui.{path}", path)
        text = value if isinstance(value, str) else path
        return _safe_format(text, fmt)

    def message(self, key: str, **fmt: Any) -> str:
        """Message (status/warning/error) by key from the ``messages`` section."""
        value = self._data.get("messages", {}).get(key, key)
        return _safe_format(value if isinstance(value, str) else key, fmt)

    def with_overrides(self, overrides: dict[str, Any]) -> AppConfig:
        """Copy with a nested dict merged on top (used by tests and ``--simulate`` tweaks)."""
        return AppConfig(_merge(copy.deepcopy(self._data), overrides))


def load_config(path: Path | None = None, overrides: dict[str, Any] | None = None) -> AppConfig:
    """Load config.json (UTF-8); a missing or broken file yields an empty config (logged)."""
    cfg_path = path or CONFIG_PATH
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _log.error("Cannot load %s: %s", cfg_path, exc)
        data = {}
    if overrides:
        _merge(data, overrides)
    return AppConfig(data)
