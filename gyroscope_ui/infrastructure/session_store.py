"""Session persistence (ARCHITECTURE section 8): ``session.json`` in the user data directory.

File content ``{"format": "gyroscope-ui-session/1", "data": {...}}``, sorted keys, UTF-8,
written atomically. An unreadable or foreign file is kept as ``session.json.bak`` and never
blocks the start.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from gyroscope_ui.infrastructure.atomic import atomic_write_text
from gyroscope_ui.infrastructure.logging import get_logger

_log = get_logger("session")

SESSION_FORMAT = "gyroscope-ui-session/1"
JSON_NAME = "session.json"


class SessionStore:
    """Reads and writes the session file in ``directory`` (thread-safe)."""

    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)
        self._lock = threading.Lock()

    @property
    def json_path(self) -> Path:
        return self.directory / JSON_NAME

    def save(self, data: dict[str, Any]) -> None:
        """Write the session atomically (OSError and TypeError propagate; the caller logs)."""
        document = {"format": SESSION_FORMAT, "data": data}
        text = json.dumps(document, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
        with self._lock:
            atomic_write_text(self.json_path, text)

    def load(self) -> dict[str, Any]:
        """The saved data; missing or damaged files give ``{}`` (never raises)."""
        with self._lock:
            path = self.json_path
            if not path.exists():
                return {}
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(document, dict) or document.get("format") != SESSION_FORMAT:
                    raise ValueError("not a gyroscope-ui session file")
                data = document.get("data")
                if not isinstance(data, dict):
                    raise ValueError("'data' is not an object")
            except (OSError, ValueError) as exc:  # JSON and Unicode decode errors are ValueErrors
                self._quarantine(path, str(exc))
                return {}
            return data

    def _quarantine(self, path: Path, reason: str) -> None:
        backup = path.with_name(path.name + ".bak")
        _log.warning("Session file %s is unusable (%s); keeping it as %s", path, reason, backup)
        try:
            os.replace(path, backup)
        except OSError as exc:
            _log.warning("Cannot rename %s: %s", path, exc)
