"""Helpers to build samples and batches in the core tests."""

from __future__ import annotations

from collections.abc import Sequence

from gyroscope_ui.core.models import Sample, SampleBatch


def make_sample(
    device_ms: int,
    *,
    seq: int | None = None,
    host_time_s: float = 0.0,
    frequency_hz: float = 10.0,
    gyro_z_rad_s: float = 1.0,
) -> Sample:
    return Sample(
        device_ms=device_ms,
        frequency_hz=frequency_hz,
        accel_x_m_s2=0.1,
        accel_y_m_s2=0.2,
        accel_z_m_s2=9.81,
        gyro_x_rad_s=0.01,
        gyro_y_rad_s=0.02,
        gyro_z_rad_s=gyro_z_rad_s,
        seq=seq,
        host_time_s=host_time_s,
    )


def make_batch(
    device_ms: Sequence[int],
    *,
    seq: Sequence[int] | None = None,
    host_time_s: Sequence[float] | None = None,
) -> SampleBatch:
    samples = [
        make_sample(
            ms,
            seq=None if seq is None else seq[i],
            host_time_s=float(i) if host_time_s is None else host_time_s[i],
        )
        for i, ms in enumerate(device_ms)
    ]
    return SampleBatch.from_samples(samples)


def steady(start_ms: int, count: int, step_ms: int = 10) -> list[int]:
    return [start_ms + i * step_ms for i in range(count)]
