"""Saving measurements: manual (file dialog, Dropbox-style folder) and automatic on Stop.

The save panel edits the save fields of the session (group letter, sub-group, suffix), the data
folder and the auto-save switch. Group and sub-group are required; missing fields are marked in
the panel. Files: the 3-column CSV plus the JSON sidecar (CONCEPT 6), written atomically by
``infrastructure.storage``; a failed save leaves the measurement unsaved.

``ask_save_path(directory, file_name) -> Path | None`` and ``ask_directory(current) -> Path |
None`` are the dialogs (replaceable in tests).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

from gyroscope_ui import __version__
from gyroscope_ui.core import naming
from gyroscope_ui.core.csv_format import csv_rows_from_recording
from gyroscope_ui.core.metadata import build_metadata
from gyroscope_ui.core.models import MeasurementInfo
from gyroscope_ui.infrastructure import storage
from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.infrastructure.logging import get_logger
from gyroscope_ui.ui.controllers.connection_controller import ConnectionController
from gyroscope_ui.ui.controllers.measurement_controller import MeasurementController
from gyroscope_ui.ui.messages import error_text, message_text
from gyroscope_ui.ui.session_state import SessionState

_log = get_logger("save")


class SaveController(QObject):
    """Signals: saved(object) with the CSV ``Path``; message(str, str) for the status bar."""

    saved = Signal(object)
    message = Signal(str, str)

    def __init__(
        self,
        config: AppConfig,
        session: SessionState,
        connection: ConnectionController,
        measurement: MeasurementController,
        *,
        today: Callable[[], date] = date.today,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._cfg = config
        self._session = session
        self._connection = connection
        self._measurement = measurement
        self._today = today
        self._panel: Any = None
        self.last_saved: Path | None = None
        self.ask_save_path: Callable[[Path, str], Path | None] = lambda _d, _n: None
        self.ask_directory: Callable[[Path], Path | None] = lambda _p: None
        measurement.stopped.connect(self._on_stopped)
        measurement.state_changed.connect(lambda _s: self._update_panel())

    # ---- configuration helpers -----------------------------------------------------------
    @property
    def _subterm_max(self) -> int:
        return int(self._cfg.get("storage.subterm_max_length", 20))

    @property
    def _weekdays(self) -> tuple[str, ...]:
        days = self._cfg.get("storage.weekday_abbreviations", naming.WEEKDAYS_DE)
        return tuple(days) if isinstance(days, list) and len(days) == 7 else naming.WEEKDAYS_DE

    @property
    def _measurement_name(self) -> str:
        return str(self._cfg.get("storage.measurement_name", "Messung"))

    # ---- actions -------------------------------------------------------------------------
    def missing_fields(self) -> set[str]:
        fields = self._session.save_fields
        missing = set()
        if not fields.group:
            missing.add("group")
        if not fields.subgroup:
            missing.add("subgroup")
        return missing

    def _check_ready(self) -> bool:
        if not self._measurement.can_save:
            self.message.emit("warning", message_text(self._cfg, "no_data_to_save"))
            return False
        missing = self.missing_fields()
        if self._panel is not None:
            self._panel.mark_missing(missing)
        if missing:
            self.message.emit("warning", message_text(self._cfg, "necessary_fields_missing"))
            return False
        return True

    def save_manual(self) -> Path | None:
        """Ask for a file in the Dropbox-style folder and save there."""
        if not self._check_ready():
            return None
        fields = self._session.save_fields
        day = self._today()
        try:
            folder = storage.manual_save_dir(
                self._session.data_dir,
                day=day,
                group=fields.group,
                tk=str(self._cfg.get("storage.tk", "TK8")),
                subterm=fields.subgroup,
                subterm_max_length=self._subterm_max,
                abbreviations=self._weekdays,
            )
            folder.mkdir(parents=True, exist_ok=True)
            number = naming.next_number((p.name for p in folder.iterdir()), day)
            proposal = naming.auto_file_name(day, number, self._measurement_name, fields.suffix)
        except (naming.NamingError, storage.StorageError) as exc:
            self.message.emit("error", error_text(self._cfg, exc))
            return None
        except OSError as exc:
            self.message.emit(
                "error",
                message_text(self._cfg, "storage_write_failed", path=str(folder), error=str(exc)),
            )
            return None
        chosen = self.ask_save_path(folder, proposal)
        if chosen is None:
            return None
        if chosen.suffix.lower() != ".csv":
            chosen = chosen.with_name(chosen.name + ".csv")
        # The file dialog has already asked before replacing an existing file.
        return self._write(chosen, overwrite=True)

    def save_auto(self) -> Path | None:
        """Save under the next free automatic name in ``<data>/<GROUP>_<subgroup>/``."""
        if not self._check_ready():
            return None
        fields = self._session.save_fields
        try:
            path = storage.auto_save_path(
                self._session.data_dir,
                day=self._today(),
                group=fields.group,
                subterm=fields.subgroup,
                suffix=fields.suffix,
                measurement_name=self._measurement_name,
                subterm_max_length=self._subterm_max,
            )
        except (naming.NamingError, storage.StorageError) as exc:
            self.message.emit("error", error_text(self._cfg, exc))
            return None
        return self._write(path, overwrite=False)

    def _write(self, path: Path, *, overwrite: bool) -> Path | None:
        m = self._measurement
        fields = self._session.save_fields
        info = MeasurementInfo(
            group=fields.group,
            subgroup=fields.subgroup,
            suffix=fields.suffix,
            start=m.start_time or m.end_time,  # type: ignore[arg-type]
            end=m.end_time,
            device=self._connection.device_info,
        )
        try:
            metadata = build_metadata(
                info=info,
                measurement_name=self._measurement_name,
                quality=m.recording.quality(),
                duration_s=m.recording.duration_s,
                app_name=str(self._cfg.get("application.name", "Gyroscope-UI")),
                app_version=__version__,
                invalid_lines=m.invalid_lines,
                abbreviations=self._weekdays,
            )
            written = storage.write_measurement(
                path, csv_rows_from_recording(m.recording), metadata, overwrite=overwrite
            )
        except (naming.NamingError, storage.StorageError) as exc:
            self.message.emit("error", error_text(self._cfg, exc))
            return None
        self.last_saved = written
        m.mark_saved()
        if self._panel is not None:
            self._panel.set_last_saved(str(written))
        self.message.emit("info", message_text(self._cfg, "data_saved", path=str(written)))
        for note in m.recording.quality().notes():
            self.message.emit("warning", message_text(self._cfg, note))
        self.saved.emit(written)
        return written

    def choose_data_dir(self) -> None:
        chosen = self.ask_directory(self._session.data_dir)
        if chosen is not None:
            self._session.set_data_dir(chosen)

    def _on_stopped(self) -> None:
        if self._session.auto_save:
            self.save_auto()

    # ---- panel binding -------------------------------------------------------------------
    def bind_panel(self, panel: Any) -> None:
        self._panel = panel
        s = self._session
        panel.save_requested.connect(self.save_manual)
        panel.group_changed.connect(lambda v: s.update_save_fields(group=v))
        panel.subgroup_changed.connect(lambda v: s.update_save_fields(subgroup=v))
        panel.suffix_changed.connect(lambda v: s.update_save_fields(suffix=v))
        panel.auto_save_toggled.connect(s.set_auto_save)
        panel.browse_requested.connect(self.choose_data_dir)
        s.data_dir_changed.connect(lambda _p: self._show_values())
        s.auto_save_changed.connect(lambda _on: self._show_values())
        self._show_values()
        panel.set_last_saved(None)
        self._update_panel()

    def _show_values(self) -> None:
        if self._panel is None:
            return
        s = self._session
        f = s.save_fields
        self._panel.set_values(f.group, f.subgroup, f.suffix, str(s.data_dir), s.auto_save)

    def _update_panel(self) -> None:
        if self._panel is None:
            return
        self._panel.set_can_save(self._measurement.can_save)
        self._panel.set_inputs_enabled(not self._measurement.is_recording)
