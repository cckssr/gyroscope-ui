"""Measurement files: atomic CSV plus JSON sidecar, and the folder and file names to use.

The CSV is byte-compatible with version 1.1.x (``csv.writer`` defaults: comma, ``\\r\\n``, UTF-8).
Naming rules live in ``core.naming``; this module only looks at the file system.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

from gyroscope_ui.core import naming
from gyroscope_ui.infrastructure.atomic import atomic_write_bytes, atomic_write_text
from gyroscope_ui.infrastructure.logging import get_logger

_log = get_logger("storage")


class StorageError(RuntimeError):
    """Saving failed; ``key`` is the message key and ``fmt`` its format arguments."""

    def __init__(self, key: str, **fmt: Any) -> None:
        self.key = key
        self.fmt = fmt
        detail = ", ".join(f"{k}={v}" for k, v in fmt.items())
        super().__init__(f"{key}: {detail}" if detail else key)


def sidecar_path(csv_path: Path) -> Path:
    """``<csv stem>.json`` next to the CSV."""
    return csv_path.with_suffix(".json")


def write_measurement(
    csv_path: Path,
    rows: list[list[str]],
    metadata: dict[str, Any],
    *,
    overwrite: bool = False,
) -> Path:
    """Write the CSV, then the JSON sidecar (both atomically); return the CSV path.

    Raises ``StorageError("file_exists")`` for an existing CSV unless ``overwrite`` and
    ``StorageError("storage_write_failed")`` for any I/O error. A CSV that was created by this
    call is removed again if its sidecar cannot be written, so a retry is not blocked by it.
    """
    csv_path = Path(csv_path)
    buffer = io.StringIO(newline="")
    csv.writer(buffer).writerows(rows)
    sidecar_text = json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    new_csv = False  # this call created the CSV (it did not replace an existing one)
    try:
        existed = csv_path.exists()
        if existed and not overwrite:
            raise StorageError("file_exists", path=str(csv_path))
        atomic_write_bytes(csv_path, buffer.getvalue().encode("utf-8"))
        new_csv = not existed
        atomic_write_text(sidecar_path(csv_path), sidecar_text)
    except OSError as exc:
        if new_csv:
            with contextlib.suppress(OSError):
                csv_path.unlink()
        _log.error("cannot write %s: %s", csv_path, exc)
        raise StorageError("storage_write_failed", path=str(csv_path), error=str(exc)) from exc
    return csv_path


def auto_save_path(
    base_dir: Path,
    *,
    day: date,
    group: str,
    subterm: str,
    suffix: str,
    measurement_name: str,
    subterm_max_length: int = 20,
) -> Path:
    """Next free ``YYYY_MM_DD-NN-name[-suffix].csv`` in ``<base>/<GROUP>_<subterm>/``.

    The folder is not created (``write_measurement`` does that).
    """
    folder = Path(base_dir) / naming.group_folder_name(group, subterm, subterm_max_length)
    try:
        existing = [p.name for p in folder.iterdir()] if folder.is_dir() else []
    except OSError as exc:
        raise StorageError("storage_write_failed", path=str(folder), error=str(exc)) from exc
    number = naming.next_number(existing, day)
    return folder / naming.auto_file_name(day, number, measurement_name, suffix)


def manual_save_dir(
    base_dir: Path,
    *,
    day: date,
    group: str,
    tk: str,
    subterm: str,
    subterm_max_length: int = 20,
    abbreviations: Sequence[str] = naming.WEEKDAYS_DE,
) -> Path:
    """Dropbox-style folder ``<base>/<Wd><GROUP><TK>[-<subterm>]`` for the save dialog.

    Not created: the UI creates it before it opens the dialog.
    """
    sanitised = naming.sanitize_subterm(subterm, subterm_max_length)
    name = naming.dropbox_folder_name(day, group, tk, sanitised, abbreviations)
    return Path(base_dir) / name
