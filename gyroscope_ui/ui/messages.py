"""Message texts for the status bar: message keys (``config.json -> messages``) plus format args.

Lower layers emit keys and format values (``DeviceError``, ``StorageError``, quality notes);
this module turns them into German text. Formatting never raises: a placeholder without a value
shows as an en dash, and a value that does not fit its format spec yields the unformatted
template.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from gyroscope_ui.infrastructure.config import AppConfig

_MISSING = "–"


class _Defaulting(dict):
    def __missing__(self, key: str) -> str:
        return _MISSING


def _display(value: Any) -> Any:
    """Tuples (ranges) read as ``200 – 1100``; everything else is passed through."""
    if isinstance(value, (tuple, list)):
        return " – ".join(f"{v:g}" if isinstance(v, (int, float)) else str(v) for v in value)
    return value


def message_text(
    config: AppConfig, key: str, details: Mapping[str, Any] | None = None, **fmt: Any
) -> str:
    """German text for ``key`` with ``details`` and ``fmt`` as format values (never raises)."""
    template = config.get(f"messages.{key}", key)
    if not isinstance(template, str):
        template = key
    values = _Defaulting({k: _display(v) for k, v in {**(details or {}), **fmt}.items()})
    try:
        return template.format_map(values)
    except (ValueError, TypeError, IndexError, AttributeError, KeyError):
        return template


def error_text(config: AppConfig, exc: BaseException) -> str:
    """Text of an exception that carries ``key`` and ``fmt`` (device / storage)."""
    key = getattr(exc, "key", None)
    if not isinstance(key, str):
        return message_text(config, "device_io_failed", error=str(exc) or type(exc).__name__)
    fmt = dict(getattr(exc, "fmt", {}) or {})
    detail = getattr(exc, "detail", "")
    if detail and "error" not in fmt:
        fmt["error"] = detail
    return message_text(config, key, **fmt)
