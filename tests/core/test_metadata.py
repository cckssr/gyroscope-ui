from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from gyroscope_ui.core.csv_format import CSV_HEADER
from gyroscope_ui.core.metadata import FORMAT, build_metadata
from gyroscope_ui.core.models import DeviceInfo, Gap, MeasurementInfo, RecordingQuality
from gyroscope_ui.core.naming import NamingError

START = datetime(2026, 11, 2, 10, 15, 0)
QUALITY = RecordingQuality(
    samples=1001,
    reordered=1,
    lost_estimated=4,
    lost_exact=3,
    restarts=1,
    gaps=(Gap(start_s=2.5, duration_s=0.4),),
)


def build(**overrides):
    info = MeasurementInfo(
        group="A",
        subgroup="Aufbau 1",
        suffix="run1",
        start=START,
        end=START + timedelta(seconds=10),
        device=DeviceInfo("E35433", "192.168.4.1", False, "1.1.1", 1),
    )
    kwargs = {
        "info": info,
        "measurement_name": "Messung",
        "quality": QUALITY,
        "duration_s": 10.0,
        "app_name": "Gyroscope-UI",
        "app_version": "2.0.0",
    }
    kwargs.update(overrides)
    return build_metadata(**kwargs)


def test_metadata_content():
    meta = build()
    assert meta["format"] == FORMAT == "gyroscope-ui-measurement/1"
    assert meta["dc:title"] == "Messung"
    assert meta["dc:creator"] == "WiSe2026_Mo_A"
    assert meta["dc:date"] == "2026-11-02"
    assert (meta["group"], meta["subgroup"], meta["suffix"]) == ("A", "Aufbau 1", "run1")
    assert meta["application"] == {"name": "Gyroscope-UI", "version": "2.0.0"}
    assert meta["samples"] == 1001 and meta["duration_s"] == 10.0
    assert meta["mean_rate_hz"] == pytest.approx(100.0)
    assert meta["columns"] == list(CSV_HEADER)
    assert meta["device"] == {
        "device_id": "E35433",
        "address": "192.168.4.1",
        "simulated": False,
        "firmware_version": "1.1.1",
        "protocol_version": 1,
    }
    assert meta["quality"]["lost_exact"] == 3
    assert meta["quality"]["invalid_lines"] == 0
    assert build(invalid_lines=7)["quality"]["invalid_lines"] == 7
    assert meta["quality"]["gaps"] == [{"start_s": 2.5, "duration_s": 0.4}]
    assert meta["quality"]["notes"] == [
        "quality_lost",
        "quality_reordered",
        "quality_restart",
        "quality_gap",
    ]


def test_times_are_iso_8601_with_an_offset():
    meta = build()
    start = datetime.fromisoformat(meta["start_time"])
    end = datetime.fromisoformat(meta["end_time"])
    assert start.utcoffset() is not None and end.utcoffset() is not None
    assert (end - start).total_seconds() == pytest.approx(10.0)
    assert start.replace(tzinfo=None) == START


def test_aware_times_keep_their_offset():
    tz = timezone(timedelta(hours=1))
    info = MeasurementInfo("B", "", "", datetime(2026, 11, 3, 9, 0, tzinfo=tz))
    meta = build(info=info)
    assert meta["start_time"].endswith("+01:00")
    assert meta["end_time"] is None and meta["device"] is None
    assert meta["dc:creator"] == "WiSe2026_Di_B"


def test_json_serialisable_and_roundtrips():
    meta = build()
    assert json.loads(json.dumps(meta, sort_keys=True)) == meta
    empty = build(quality=RecordingQuality(), duration_s=0.0)
    assert json.loads(json.dumps(empty)) == empty
    assert empty["mean_rate_hz"] == 0.0 and empty["quality"]["lost_exact"] is None


def test_invalid_group_raises_a_naming_error():
    info = MeasurementInfo("", "", "", START)
    with pytest.raises(NamingError):
        build(info=info)
