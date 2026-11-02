"""Content of the JSON sidecar next to every CSV (CONCEPT 6.3).

Returns plain JSON-serialisable data; writing the file is up to ``infrastructure.storage``.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from gyroscope_ui.core.csv_format import CSV_HEADER
from gyroscope_ui.core.models import DeviceInfo, MeasurementInfo, RecordingQuality
from gyroscope_ui.core.naming import WEEKDAYS_DE, group_name

FORMAT = "gyroscope-ui-measurement/1"


def _with_offset(moment: datetime) -> datetime:
    """Naive datetimes are local time; aware ones are left alone (no conversion)."""
    return moment if moment.tzinfo is not None else moment.astimezone()


def _device_dict(device: DeviceInfo | None) -> dict[str, Any] | None:
    if device is None:
        return None
    return {
        "device_id": device.device_id,
        "address": device.address,
        "simulated": device.simulated,
        "firmware_version": device.firmware_version,
        "protocol_version": device.protocol_version,
    }


def _quality_dict(quality: RecordingQuality, invalid_lines: int) -> dict[str, Any]:
    return {
        "samples": quality.samples,
        "invalid_lines": invalid_lines,
        "reordered": quality.reordered,
        "lost_estimated": quality.lost_estimated,
        "lost_exact": quality.lost_exact,
        "restarts": quality.restarts,
        "gaps": [{"start_s": g.start_s, "duration_s": g.duration_s} for g in quality.gaps],
        "notes": list(quality.notes()),
    }


def build_metadata(
    *,
    info: MeasurementInfo,
    measurement_name: str,
    quality: RecordingQuality,
    duration_s: float,
    app_name: str,
    app_version: str,
    invalid_lines: int = 0,
    abbreviations: Sequence[str] = WEEKDAYS_DE,
) -> dict[str, Any]:
    """Metadata of one measurement; naive datetimes are taken as local time, aware ones keep
    their offset.

    ``invalid_lines`` is the link's count of rejected lines during the recording (``LinkStats``).

    Raises ``NamingError`` if ``info.group`` is not a letter A-Z.
    """
    start = _with_offset(info.start)
    end = _with_offset(info.end) if info.end is not None else None
    samples = quality.samples
    mean_rate_hz = (samples - 1) / duration_s if samples > 1 and duration_s > 0 else 0.0
    return {
        "format": FORMAT,
        "dc:title": measurement_name,
        "dc:creator": group_name(start.date(), info.group, abbreviations),
        "dc:date": start.date().isoformat(),
        "group": info.group,
        "subgroup": info.subgroup,
        "suffix": info.suffix,
        "start_time": start.isoformat(),
        "end_time": end.isoformat() if end is not None else None,
        "device": _device_dict(info.device),
        "application": {"name": app_name, "version": app_version},
        "samples": samples,
        "duration_s": duration_s,
        "mean_rate_hz": mean_rate_hz,
        "quality": _quality_dict(quality, invalid_lines),
        "columns": list(CSV_HEADER),
    }
