"""Dataclasses shared by all layers: the contract between core, infrastructure and ui.

Everything here is frozen and Qt-free. Signals carry these objects, primitives or NumPy arrays.
Arrays inside frozen dataclasses are read-only (``flags.writeable = False``).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

import numpy as np

CHANNELS: tuple[str, ...] = (
    "frequency_hz",
    "accel_x_m_s2",
    "accel_y_m_s2",
    "accel_z_m_s2",
    "gyro_x_rad_s",
    "gyro_y_rad_s",
    "gyro_z_rad_s",
)
BATCH_COLUMNS: tuple[str, ...] = ("device_ms", "seq", "host_time_s", *CHANNELS)
NO_SEQ = -1  # sentinel for "no sequence number" in integer arrays


class LinkState(StrEnum):
    """Connection state of the device link (CONCEPT 4.1)."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STALE = "stale"
    LOST = "lost"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class Sample:
    """One parsed data line. ``frequency_hz`` is already divided by the pulses per revolution."""

    device_ms: int
    frequency_hz: float
    accel_x_m_s2: float
    accel_y_m_s2: float
    accel_z_m_s2: float
    gyro_x_rad_s: float
    gyro_y_rad_s: float
    gyro_z_rad_s: float
    seq: int | None = None
    host_time_s: float = 0.0  # host monotonic clock (``time.monotonic()``) at reception


def _frozen(array: np.ndarray) -> np.ndarray:
    array.flags.writeable = False
    return array


@dataclass(frozen=True, eq=False)
class SampleBatch:
    """Columnar form of many samples (what the worker emits); all arrays have the same length."""

    device_ms: np.ndarray  # int64
    seq: np.ndarray  # int64, ``NO_SEQ`` = none
    host_time_s: np.ndarray  # float64
    frequency_hz: np.ndarray
    accel_x_m_s2: np.ndarray
    accel_y_m_s2: np.ndarray
    accel_z_m_s2: np.ndarray
    gyro_x_rad_s: np.ndarray
    gyro_y_rad_s: np.ndarray
    gyro_z_rad_s: np.ndarray

    def __post_init__(self) -> None:
        for name in BATCH_COLUMNS:
            _frozen(getattr(self, name))

    @classmethod
    def from_samples(cls, samples: Sequence[Sample]) -> SampleBatch:
        """Build a batch from samples (an empty sequence gives an empty batch)."""
        n = len(samples)
        device_ms = np.fromiter((s.device_ms for s in samples), dtype=np.int64, count=n)
        seq = np.fromiter(
            (NO_SEQ if s.seq is None else s.seq for s in samples), dtype=np.int64, count=n
        )
        host = np.fromiter((s.host_time_s for s in samples), dtype=np.float64, count=n)
        channels = {
            name: np.fromiter((getattr(s, name) for s in samples), dtype=np.float64, count=n)
            for name in CHANNELS
        }
        return cls(device_ms=device_ms, seq=seq, host_time_s=host, **channels)

    @classmethod
    def empty(cls) -> SampleBatch:
        return cls.from_samples(())

    def __len__(self) -> int:
        return len(self.device_ms)

    def select(self, mask: np.ndarray) -> SampleBatch:
        """Sub-batch of the samples where the boolean ``mask`` is true."""
        return SampleBatch(**{name: self.column(name)[mask] for name in BATCH_COLUMNS})

    def column(self, name: str) -> np.ndarray:
        """Array of ``name`` (``device_ms``, ``seq``, ``host_time_s`` or a channel)."""
        if name not in BATCH_COLUMNS:
            raise KeyError(name)
        return getattr(self, name)


@dataclass(frozen=True)
class DeviceInfo:
    """Identity of the connected device (real or simulated)."""

    device_id: str
    address: str
    simulated: bool = False
    firmware_version: str | None = None
    protocol_version: int | None = None


@dataclass(frozen=True)
class Gap:
    """A stretch without data inside a recording."""

    start_s: float  # elapsed time of the last sample before the gap
    duration_s: float


@dataclass(frozen=True)
class RecordingQuality:
    """Counters of one recording; goes into the metadata sidecar."""

    samples: int = 0
    reordered: int = 0
    lost_estimated: int = 0
    lost_exact: int | None = None  # None until sequence numbers were seen
    restarts: int = 0
    gaps: tuple[Gap, ...] = ()

    def notes(self) -> tuple[str, ...]:
        """Message keys for the non-zero counters (the UI turns them into German text)."""
        notes: list[str] = []
        if self.lost_exact or self.lost_estimated:
            notes.append("quality_lost")
        if self.reordered:
            notes.append("quality_reordered")
        if self.restarts:
            notes.append("quality_restart")
        if self.gaps:
            notes.append("quality_gap")
        return tuple(notes)


@dataclass(frozen=True)
class LinkStats:
    """Counters of the device link since ``open()``."""

    rate_hz: float = 0.0
    received: int = 0
    invalid: int = 0
    data_age_s: float | None = None  # None: no data yet
    protocol_version: int | None = None


@dataclass(frozen=True)
class ChannelStatistics:
    """Population statistics of one channel; NaN values are ignored."""

    count: int
    minimum: float
    maximum: float
    mean: float
    std: float

    @classmethod
    def of(cls, values: np.ndarray) -> ChannelStatistics:
        finite = values[~np.isnan(values)]
        if finite.size == 0:
            nan = math.nan
            return cls(0, nan, nan, nan, nan)
        return cls(
            count=int(finite.size),
            minimum=float(finite.min()),
            maximum=float(finite.max()),
            mean=float(finite.mean()),
            std=float(finite.std()),
        )


@dataclass(frozen=True)
class MeasurementInfo:
    """What the user entered plus timing; input of the file naming and the metadata."""

    group: str
    subgroup: str
    suffix: str
    start: datetime
    end: datetime | None = None
    device: DeviceInfo | None = None
