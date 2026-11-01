"""Rows of the saved CSV (CONCEPT 6.1): three columns, byte-compatible with version 1.1.x.

This module only builds the rows; the writer (``infrastructure.storage``) uses ``csv.writer``
defaults (comma, ``\\r\\n``).
"""

from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np

from gyroscope_ui.core.recording import Recording

CSV_HEADER: tuple[str, ...] = (
    "Time (s)",
    "Disk rotation frequency (Hz)",
    "Gyro Z rate (rad/s)",
)


def _cell(value: float) -> str:
    """``%.6f``; an empty cell for NaN."""
    return "" if math.isnan(value) else f"{value:.6f}"


def _floats(values: Iterable[float]) -> list[float]:
    return values.tolist() if isinstance(values, np.ndarray) else [float(v) for v in values]


def csv_rows(
    elapsed_s: Iterable[float],
    frequency_hz: Iterable[float],
    gyro_z_rad_s: Iterable[float],
) -> list[list[str]]:
    """Header row followed by one row per sample."""
    rows = [list(CSV_HEADER)]
    for t_s, freq, gyro_z in zip(
        _floats(elapsed_s), _floats(frequency_hz), _floats(gyro_z_rad_s), strict=True
    ):
        rows.append([f"{t_s:.6f}", _cell(freq), _cell(gyro_z)])
    return rows


def csv_rows_from_recording(recording: Recording) -> list[list[str]]:
    return csv_rows(
        recording.column("elapsed_s"),
        recording.column("frequency_hz"),
        recording.column("gyro_z_rad_s"),
    )
