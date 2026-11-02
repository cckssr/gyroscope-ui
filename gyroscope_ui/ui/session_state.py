"""Shared session state: the single owner of the values several controllers and tabs share.

Holds the save fields (group letter, sub-group, suffix), the data folder, the auto-save switch,
the display options and an opaque JSON dict per namespace (:meth:`ui_state`, e.g. the window
layout), each with a change signal. Persists through :class:`SessionStore`: restored on
construction, saved debounced after every change (``session.debounce_s``) and synchronously on
:meth:`shutdown`.

The save fields belong to one lab group: they are restored only within
``session.group_valid_days`` calendar days (default 1, i.e. the same day) of their last change,
so the next day's group starts with empty fields (CONCEPT section 8).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal

from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.infrastructure.logging import get_logger
from gyroscope_ui.infrastructure.paths import AppPaths
from gyroscope_ui.infrastructure.session_store import SessionStore

_log = get_logger("session_state")
_STATE_VERSION = 1


@dataclass(frozen=True)
class SaveFields:
    """What the save panel collects; ``group`` is a letter A-Z or empty."""

    group: str = ""
    subgroup: str = ""
    suffix: str = ""


@dataclass(frozen=True)
class DisplayOptions:
    auto_scroll: bool = True
    scroll_window_s: float = 60.0
    all_channels: bool = False


class SessionState(QObject):
    """See the module docstring. All methods are for the GUI thread.

    ``today`` is injectable so tests can move the calendar.
    """

    save_fields_changed = Signal(object)  # SaveFields
    data_dir_changed = Signal(object)  # Path
    auto_save_changed = Signal(bool)
    display_changed = Signal(object)  # DisplayOptions
    ui_state_changed = Signal(str)  # namespace
    message = Signal(str, str)  # level ("info" | "warning" | "error"), text

    def __init__(
        self,
        config: AppConfig,
        paths: AppPaths,
        parent: QObject | None = None,
        *,
        persist: bool = True,
        today: Any = date.today,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.paths = paths
        self._today = today
        self._fields = SaveFields()
        self._fields_date: date | None = None
        self._data_dir = self._default_data_dir()
        self._auto_save = False
        self._display = DisplayOptions(
            auto_scroll=bool(config.get("display.auto_scroll", True)),
            scroll_window_s=float(config.get("display.scroll_window_s", 60.0)),
            all_channels=bool(config.get("display.all_channels", False)),
        )
        self._ui_state: dict[str, dict[str, Any]] = {}

        self._store: SessionStore | None = SessionStore(paths.session_dir) if persist else None
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(
            max(0, int(float(config.get("session.debounce_s", 1.0)) * 1000))
        )
        self._save_timer.timeout.connect(self.save_now)
        self._restore()

    def _default_data_dir(self) -> Path:
        configured = self.config.get("application.data_dir", "")
        return Path(configured) if configured else AppPaths.default_data_dir()

    # ---- save fields ---------------------------------------------------------------------
    @property
    def save_fields(self) -> SaveFields:
        return self._fields

    def update_save_fields(self, **changes: str) -> None:
        """Change ``group``, ``subgroup`` and / or ``suffix`` (whitespace is stripped)."""
        fields = replace(self._fields, **{k: str(v).strip() for k, v in changes.items()})
        if fields != self._fields:
            self._fields = fields
            self._fields_date = self._today()
            self.save_fields_changed.emit(fields)
            self._mark_dirty()

    # ---- data folder and auto-save -------------------------------------------------------
    @property
    def data_dir(self) -> Path:
        return self._data_dir

    def set_data_dir(self, path: Path) -> None:
        path = Path(path)
        if path != self._data_dir:
            self._data_dir = path
            self.data_dir_changed.emit(path)
            self._mark_dirty()

    @property
    def auto_save(self) -> bool:
        return self._auto_save

    def set_auto_save(self, on: bool) -> None:
        on = bool(on)
        if on != self._auto_save:
            self._auto_save = on
            self.auto_save_changed.emit(on)
            self._mark_dirty()

    # ---- display options -----------------------------------------------------------------
    @property
    def display(self) -> DisplayOptions:
        return self._display

    def update_display(self, **changes: Any) -> None:
        display = replace(self._display, **changes)
        if display != self._display:
            self._display = display
            self.display_changed.emit(display)
            self._mark_dirty()

    # ---- opaque UI state -----------------------------------------------------------------
    def ui_state(self, namespace: str) -> dict[str, Any]:
        """The (mutable, JSON-compatible) state dict of ``namespace``, created on demand.

        Change it in place and call :meth:`touch_ui_state`, or replace it with
        :meth:`set_ui_state`.
        """
        return self._ui_state.setdefault(namespace, {})

    def set_ui_state(self, namespace: str, state: dict[str, Any]) -> None:
        self._ui_state[namespace] = state
        self.touch_ui_state(namespace)

    def touch_ui_state(self, namespace: str) -> None:
        """Announce and persist an in-place change of ``ui_state(namespace)``."""
        self.ui_state_changed.emit(namespace)
        self._mark_dirty()

    # ---- persistence ---------------------------------------------------------------------
    def _mark_dirty(self) -> None:
        if self._store is not None and not self._save_timer.isActive():
            self._save_timer.start()

    def _state_dict(self) -> dict[str, Any]:
        return {
            "version": _STATE_VERSION,
            "save_fields": {
                "group": self._fields.group,
                "subgroup": self._fields.subgroup,
                "suffix": self._fields.suffix,
                "date": self._fields_date.isoformat() if self._fields_date else None,
            },
            "data_dir": str(self._data_dir),
            "auto_save": self._auto_save,
            "display": {
                "auto_scroll": self._display.auto_scroll,
                "scroll_window_s": self._display.scroll_window_s,
                "all_channels": self._display.all_channels,
            },
            "ui": self._ui_state,
        }

    def save_now(self) -> bool:
        """Write the session file now; True on success (or when persistence is off)."""
        self._save_timer.stop()
        if self._store is None:
            return True
        try:
            self._store.save(self._state_dict())
        except (OSError, ValueError, TypeError) as exc:
            _log.error("cannot save the session: %s", exc)
            return False
        return True

    def _fields_still_valid(self, stamp: Any) -> bool:
        if not isinstance(stamp, str):
            return False
        try:
            entered = date.fromisoformat(stamp)
        except ValueError:
            return False
        days = int(self.config.get("session.group_valid_days", 1))
        return 0 <= (self._today() - entered).days < max(days, 0)

    def _restore(self) -> None:
        if self._store is None:
            return
        state = self._store.load()
        fields = state.get("save_fields")
        if isinstance(fields, dict) and self._fields_still_valid(fields.get("date")):
            self._fields = SaveFields(
                group=str(fields.get("group", "") or ""),
                subgroup=str(fields.get("subgroup", "") or ""),
                suffix=str(fields.get("suffix", "") or ""),
            )
            self._fields_date = date.fromisoformat(fields["date"])
        if isinstance(state.get("data_dir"), str) and state["data_dir"]:
            self._data_dir = Path(state["data_dir"])
        self._auto_save = bool(state.get("auto_save", False))
        display = state.get("display")
        if isinstance(display, dict):
            try:
                self._display = DisplayOptions(
                    auto_scroll=bool(display.get("auto_scroll", self._display.auto_scroll)),
                    scroll_window_s=float(
                        display.get("scroll_window_s", self._display.scroll_window_s)
                    ),
                    all_channels=bool(display.get("all_channels", self._display.all_channels)),
                )
            except (TypeError, ValueError) as exc:
                _log.warning("ignoring unreadable display options in the session: %s", exc)
        ui = state.get("ui")
        if isinstance(ui, dict):
            self._ui_state = {str(k): v for k, v in ui.items() if isinstance(v, dict)}

    def shutdown(self) -> None:
        """Synchronous final save (window close)."""
        self._save_timer.stop()
        self.save_now()
