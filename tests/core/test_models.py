from __future__ import annotations

import dataclasses
import math
from datetime import datetime

import numpy as np
import pytest
from batches import make_sample

from gyroscope_ui.core.models import (
    CHANNELS,
    ChannelStatistics,
    DeviceInfo,
    Gap,
    LinkState,
    MeasurementInfo,
    RecordingQuality,
    Sample,
    SampleBatch,
)


def test_link_state_values():
    assert [s.value for s in LinkState] == [
        "disconnected",
        "connecting",
        "connected",
        "stale",
        "lost",
        "error",
    ]
    assert LinkState("stale") is LinkState.STALE


def test_sample_is_frozen_with_defaults():
    sample = make_sample(5)
    assert sample.seq is None and sample.host_time_s == 0.0
    with pytest.raises(dataclasses.FrozenInstanceError):
        sample.device_ms = 6  # type: ignore[misc]


def test_channels_follow_the_sample_field_order():
    fields = [f.name for f in dataclasses.fields(Sample)]
    assert tuple(fields[1:8]) == CHANNELS
    assert CHANNELS[0] == "frequency_hz" and CHANNELS[-1] == "gyro_z_rad_s"


def test_batch_from_samples_columns_and_dtypes():
    batch = SampleBatch.from_samples(
        [make_sample(10, seq=4, host_time_s=1.5), make_sample(20, host_time_s=1.6)]
    )
    assert len(batch) == 2
    assert batch.device_ms.dtype == np.int64 and batch.seq.dtype == np.int64
    assert batch.device_ms.tolist() == [10, 20]
    assert batch.seq.tolist() == [4, -1]
    assert batch.host_time_s.tolist() == [1.5, 1.6]
    for name in CHANNELS:
        assert batch.column(name).dtype == np.float64
    assert batch.column("gyro_z_rad_s").tolist() == [1.0, 1.0]


def test_batch_arrays_are_read_only():
    batch = SampleBatch.from_samples([make_sample(1)])
    with pytest.raises(ValueError, match="read-only"):
        batch.device_ms[0] = 2
    with pytest.raises(ValueError, match="read-only"):
        batch.column("frequency_hz")[0] = 2.0


def test_empty_batch():
    batch = SampleBatch.empty()
    assert len(batch) == 0
    assert batch.column("frequency_hz").shape == (0,)


def test_batch_select_and_unknown_column():
    batch = SampleBatch.from_samples([make_sample(i * 10) for i in range(4)])
    picked = batch.select(np.array([True, False, True, False]))
    assert picked.device_ms.tolist() == [0, 20]
    with pytest.raises(KeyError):
        batch.column("nope")


def test_device_info_defaults():
    info = DeviceInfo(device_id="E35433", address="192.168.4.1")
    assert not info.simulated and info.firmware_version is None and info.protocol_version is None


def test_quality_notes_are_keys_for_nonzero_counters():
    assert RecordingQuality().notes() == ()
    quality = RecordingQuality(
        samples=10, reordered=1, lost_estimated=3, restarts=1, gaps=(Gap(1.0, 0.5),)
    )
    assert quality.notes() == (
        "quality_lost",
        "quality_reordered",
        "quality_restart",
        "quality_gap",
    )
    assert RecordingQuality(lost_exact=2).notes() == ("quality_lost",)
    assert RecordingQuality(lost_exact=0).notes() == ()


def test_statistics_ignore_nan():
    stats = ChannelStatistics.of(np.array([1.0, math.nan, 3.0, 5.0]))
    assert stats.count == 3
    assert (stats.minimum, stats.maximum) == (1.0, 5.0)
    assert stats.mean == pytest.approx(3.0)
    assert stats.std == pytest.approx(np.std([1.0, 3.0, 5.0]))  # population std


@pytest.mark.parametrize("values", [np.array([]), np.array([math.nan, math.nan])])
def test_statistics_of_nothing(values):
    stats = ChannelStatistics.of(values)
    assert stats.count == 0
    assert all(math.isnan(v) for v in (stats.minimum, stats.maximum, stats.mean, stats.std))


def test_measurement_info_defaults():
    info = MeasurementInfo(group="A", subgroup="x", suffix="", start=datetime(2026, 11, 2, 10))
    assert info.end is None and info.device is None
