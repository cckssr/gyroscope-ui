"""Recording of one measurement and the rolling preview buffer.

``Recording`` stores every accepted sample in chunked NumPy arrays (amortised O(batch) appends,
no copy of old data) and runs the incoming batches through a ``TimeBase``. ``RollingBuffer`` is
the fixed-size ring buffer behind the live preview outside a recording.
"""

from __future__ import annotations

import numpy as np

from gyroscope_ui.core.models import (
    CHANNELS,
    ChannelStatistics,
    RecordingQuality,
    SampleBatch,
)
from gyroscope_ui.core.timebase import TimeBase

CHUNK_SIZE = 8192
_DTYPES: dict[str, type] = {
    "elapsed_s": np.float64,
    "device_ms": np.int64,
    "seq": np.int64,
    "host_time_s": np.float64,
    **dict.fromkeys(CHANNELS, np.float64),
}
COLUMNS: tuple[str, ...] = tuple(_DTYPES)


class Recording:
    """All samples of one measurement; only samples received after ``start`` are accepted."""

    def __init__(self, chunk_size: int = CHUNK_SIZE, timebase: TimeBase | None = None) -> None:
        self._chunk_size = chunk_size
        self._timebase = timebase if timebase is not None else TimeBase()
        self._chunks: dict[str, list[np.ndarray]] = {name: [] for name in COLUMNS}
        self._count = 0
        self._recording = False
        self._start_host_time_s: float | None = None
        self._last_elapsed = 0.0
        self._cache: dict[str, np.ndarray] = {}

    # --- state -------------------------------------------------------------------------------

    def start(self, host_time_s: float) -> None:
        """Clear the data and begin recording samples received at or after ``host_time_s``."""
        self._clear()
        self._recording = True
        self._start_host_time_s = host_time_s

    def stop(self) -> None:
        self._recording = False

    def reset(self) -> None:
        """Stop and discard all data."""
        self._clear()
        self._recording = False
        self._start_host_time_s = None

    def _clear(self) -> None:
        self._chunks = {name: [] for name in COLUMNS}
        self._count = 0
        self._last_elapsed = 0.0
        self._cache.clear()
        self._timebase.reset()

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def start_host_time_s(self) -> float | None:
        return self._start_host_time_s

    def __len__(self) -> int:
        return self._count

    @property
    def duration_s(self) -> float:
        return self._last_elapsed

    # --- data --------------------------------------------------------------------------------

    def append(self, batch: SampleBatch) -> int:
        """Store the acceptable samples of ``batch``; returns how many were stored.

        Samples received before ``start`` (D3) are ignored, the rest passes the time base.
        """
        if not self._recording or len(batch) == 0 or self._start_host_time_s is None:
            return 0
        fresh = batch.host_time_s >= self._start_host_time_s
        if not fresh.all():
            batch = batch.select(fresh)
            if len(batch) == 0:
                return 0
        elapsed, accepted = self._timebase.process(batch)
        if not accepted.all():
            batch = batch.select(accepted)
        stored = len(elapsed)
        if stored == 0:
            return 0
        self._store("elapsed_s", elapsed)
        for name in COLUMNS[1:]:
            self._store(name, batch.column(name))
        self._count += stored
        self._last_elapsed = float(elapsed[-1])
        self._cache.clear()
        return stored

    def _store(self, name: str, values: np.ndarray) -> None:
        """Write ``values`` at the current end of column ``name`` (``_count`` is advanced later)."""
        chunks = self._chunks[name]
        size = self._chunk_size
        position = self._count
        done = 0
        while done < len(values):
            index, used = divmod(position, size)
            if index == len(chunks):
                chunks.append(np.empty(size, dtype=_DTYPES[name]))
            take = min(size - used, len(values) - done)
            chunks[index][used : used + take] = values[done : done + take]
            done += take
            position += take

    def column(self, name: str) -> np.ndarray:
        """Read-only contiguous copy of a column, cached until the next ``append``.

        Names: ``elapsed_s``, ``device_ms``, ``seq`` (-1 = none), ``host_time_s`` and ``CHANNELS``.
        """
        if name not in _DTYPES:
            raise KeyError(name)
        cached = self._cache.get(name)
        if cached is not None:
            return cached
        chunks = self._chunks[name]
        if chunks:
            last_used = self._count - (len(chunks) - 1) * self._chunk_size
            values = np.concatenate([*chunks[:-1], chunks[-1][:last_used]])
        else:
            values = np.empty(0, dtype=_DTYPES[name])
        values.flags.writeable = False
        self._cache[name] = values
        return values

    def statistics(
        self, name: str, t0_s: float | None = None, t1_s: float | None = None
    ) -> ChannelStatistics:
        """Statistics of ``name`` over the elapsed-time window ``[t0_s, t1_s]`` (default: all)."""
        values = self.column(name)
        if t0_s is not None or t1_s is not None:
            elapsed = self.column("elapsed_s")  # non-decreasing, so a binary search is enough
            lo = 0 if t0_s is None else int(np.searchsorted(elapsed, t0_s, side="left"))
            hi = len(elapsed) if t1_s is None else int(np.searchsorted(elapsed, t1_s, side="right"))
            values = values[lo:hi]
        return ChannelStatistics.of(values.astype(np.float64, copy=False))

    def quality(self) -> RecordingQuality:
        return self._timebase.quality(self._count)


class RollingBuffer:
    """Ring buffer of the newest samples for the live preview, at most ``capacity`` of them.

    The storage grows on demand (doubling), so a large capacity costs nothing until the samples
    have actually arrived."""

    _NAMES = ("host_time_s", *CHANNELS)
    _INITIAL = 4096  # samples allocated up front

    def __init__(self, capacity: int) -> None:
        self._capacity = max(1, capacity)
        self._alloc = min(self._capacity, self._INITIAL)
        self._data = np.empty((len(self._NAMES), self._alloc), dtype=np.float64)
        self._size = 0
        self._head = 0  # index of the oldest sample once the buffer is full

    @property
    def capacity(self) -> int:
        return self._capacity

    def __len__(self) -> int:
        return self._size

    def clear(self) -> None:
        self._size = 0
        self._head = 0

    def extend(self, batch: SampleBatch) -> None:
        """Append a batch; only the newest ``capacity`` samples are kept."""
        n = len(batch)
        if n == 0:
            return
        start = max(0, n - self._capacity)
        count = n - start
        self._reserve(min(self._capacity, self._size + count))
        cap = self._alloc  # == capacity as soon as samples are overwritten
        # write position of the first kept sample (the oldest samples are overwritten)
        first = (self._head + self._size) % cap
        index = (first + np.arange(count)) % cap
        for row, name in enumerate(self._NAMES):
            self._data[row, index] = batch.column(name)[start:]
        overflow = self._size + count - cap
        if overflow > 0:
            self._head = (self._head + overflow) % cap
            self._size = cap
        else:
            self._size += count

    def _reserve(self, needed: int) -> None:
        """Make the storage hold ``needed`` samples (``needed`` <= capacity)."""
        if needed <= self._alloc:
            return
        self._relocate(min(self._capacity, max(needed, 2 * self._alloc)))

    def _relocate(self, alloc: int) -> None:
        """Move the samples, oldest first, into fresh storage of ``alloc`` slots."""
        keep = min(self._size, alloc)
        old = {name: self.column(name)[self._size - keep :] for name in self._NAMES}
        self._alloc = alloc
        self._data = np.empty((len(self._NAMES), alloc), dtype=np.float64)
        for row, name in enumerate(self._NAMES):
            self._data[row, :keep] = old[name]
        self._size = keep
        self._head = 0

    def column(self, name: str) -> np.ndarray:
        """Chronological copy of ``host_time_s`` or a channel."""
        row = self._NAMES.index(name)
        order = (self._head + np.arange(self._size)) % self._alloc
        return self._data[row, order]

    def latest(self) -> dict[str, float] | None:
        """Newest sample as ``{name: value}`` (``host_time_s`` and all channels), or ``None``."""
        if self._size == 0:
            return None
        newest = (self._head + self._size - 1) % self._alloc
        return {name: float(self._data[row, newest]) for row, name in enumerate(self._NAMES)}

    def resize(self, capacity: int) -> None:
        """Change the capacity, keeping the newest samples."""
        capacity = max(1, capacity)
        if capacity == self._capacity:
            return
        self._capacity = capacity
        self._relocate(min(capacity, max(self._size, self._alloc)))
