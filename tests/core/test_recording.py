from __future__ import annotations

import math
import time

import numpy as np
import pytest
from batches import make_batch, make_sample, steady

from gyroscope_ui.core.models import CHANNELS, SampleBatch
from gyroscope_ui.core.recording import COLUMNS, Recording, RollingBuffer


def batch_at(device_ms, host_start: float = 100.0, **kwargs) -> SampleBatch:
    host = [host_start + i * 0.01 for i in range(len(device_ms))]
    return make_batch(device_ms, host_time_s=host, **kwargs)


def test_nothing_is_stored_before_start_or_after_stop():
    rec = Recording()
    assert rec.append(batch_at(steady(0, 5))) == 0 and len(rec) == 0
    rec.start(100.0)
    assert rec.is_recording and rec.start_host_time_s == 100.0
    assert rec.append(batch_at(steady(0, 5))) == 5
    rec.stop()
    assert not rec.is_recording
    assert rec.append(batch_at(steady(50, 5))) == 0
    assert len(rec) == 5


def test_d3_samples_received_before_start_are_not_recorded():
    """D3: queued samples from before Start must never become the first rows."""
    rec = Recording()
    rec.start(10.0)
    batch = make_batch(
        [100, 110, 120, 130, 140],
        host_time_s=[9.0, 9.5, 9.999, 10.0, 10.5],
    )
    assert rec.append(batch) == 2
    assert rec.column("device_ms").tolist() == [130, 140]
    assert rec.column("elapsed_s").tolist() == pytest.approx([0.0, 0.01])


def test_d3_a_batch_entirely_before_start_is_ignored():
    rec = Recording()
    rec.start(10.0)
    assert rec.append(make_batch([1, 2, 3], host_time_s=[1.0, 2.0, 3.0])) == 0
    assert len(rec) == 0 and rec.duration_s == 0.0


def test_d4_restart_mid_recording_keeps_all_later_samples():
    """D4: the old code dropped everything after a reboot until the old maximum was exceeded."""
    rec = Recording()
    rec.start(0.0)
    first = steady(0, 500)  # 5 s of uptime
    second = steady(0, 300)  # device reboots, 3 more seconds
    assert rec.append(batch_at(first)) == 500
    assert rec.append(batch_at(second, host_start=200.0)) == 300
    elapsed = rec.column("elapsed_s")
    assert len(rec) == 800 and len(elapsed) == 800
    assert np.all(np.diff(elapsed) > 0)
    assert elapsed[500] == pytest.approx(elapsed[499] + 0.01)
    assert rec.duration_s == pytest.approx(elapsed[-1])
    assert rec.quality().restarts == 1
    assert rec.quality().samples == 800


def test_reordered_samples_are_dropped_and_counted():
    rec = Recording()
    rec.start(0.0)
    assert rec.append(batch_at([*steady(0, 6), 25, *steady(60, 2)])) == 8
    assert 25 not in rec.column("device_ms").tolist()
    assert rec.quality().reordered == 1


def test_chunk_boundaries_and_column_content():
    rec = Recording(chunk_size=4)
    rec.start(0.0)
    total = 0
    for size in (3, 1, 9, 5, 2, 8):
        total += rec.append(batch_at(steady(total * 10, size)))
    assert len(rec) == total == 28
    assert rec.column("device_ms").tolist() == [i * 10 for i in range(28)]
    assert rec.column("elapsed_s").tolist() == pytest.approx([i * 0.01 for i in range(28)])
    assert rec.column("seq").tolist() == [-1] * 28
    assert rec.column("frequency_hz").tolist() == [10.0] * 28


def test_every_column_is_available_read_only_and_typed():
    rec = Recording()
    rec.start(0.0)
    rec.append(batch_at(steady(0, 3), seq=[7, 8, 9]))
    assert set(COLUMNS) == {"elapsed_s", "device_ms", "seq", "host_time_s", *CHANNELS}
    for name in COLUMNS:
        column = rec.column(name)
        assert len(column) == 3 and column.flags["C_CONTIGUOUS"]
        with pytest.raises(ValueError, match="read-only"):
            column[0] = 1
    assert rec.column("device_ms").dtype == np.int64
    assert rec.column("seq").tolist() == [7, 8, 9]
    with pytest.raises(KeyError):
        rec.column("nope")


def test_column_is_cached_until_the_next_append():
    rec = Recording()
    rec.start(0.0)
    rec.append(batch_at(steady(0, 3)))
    first = rec.column("elapsed_s")
    assert rec.column("elapsed_s") is first
    rec.append(batch_at(steady(30, 2)))
    assert rec.column("elapsed_s") is not first
    assert len(rec.column("elapsed_s")) == 5
    assert len(first) == 3  # an earlier copy is unaffected


def test_start_clears_and_reset_discards():
    rec = Recording()
    rec.start(0.0)
    rec.append(batch_at(steady(0, 10)))
    rec.start(500.0)
    assert len(rec) == 0 and rec.duration_s == 0.0 and rec.quality().samples == 0
    rec.append(make_batch(steady(9000, 3), host_time_s=[500.0, 500.1, 500.2]))
    assert rec.column("elapsed_s")[0] == 0.0  # new base
    rec.reset()
    assert len(rec) == 0 and not rec.is_recording and rec.start_host_time_s is None
    assert rec.column("elapsed_s").shape == (0,)


def test_duration_is_the_last_elapsed_time():
    rec = Recording()
    assert rec.duration_s == 0.0
    rec.start(0.0)
    rec.append(batch_at(steady(0, 101)))
    assert rec.duration_s == pytest.approx(1.0)


def test_statistics_over_all_and_over_a_window():
    rec = Recording()
    rec.start(0.0)
    batch = SampleBatch.from_samples(
        [make_sample(i * 10, host_time_s=float(i), frequency_hz=float(i)) for i in range(11)]
    )
    rec.append(batch)  # elapsed 0.00 ... 0.10, frequency 0 ... 10
    everything = rec.statistics("frequency_hz")
    assert (everything.count, everything.minimum, everything.maximum) == (11, 0.0, 10.0)
    assert everything.mean == pytest.approx(5.0)
    window = rec.statistics("frequency_hz", 0.03, 0.06)
    assert (window.count, window.minimum, window.maximum) == (4, 3.0, 6.0)
    assert rec.statistics("frequency_hz", t0_s=0.09).count == 2
    assert rec.statistics("frequency_hz", t1_s=0.01).count == 2
    assert rec.statistics("frequency_hz", 5.0, 6.0).count == 0


def test_statistics_ignore_nan_values():
    rec = Recording()
    rec.start(0.0)
    values = [1.0, math.nan, 3.0, math.nan]
    rec.append(
        SampleBatch.from_samples(
            [
                make_sample(i * 10, host_time_s=float(i), frequency_hz=v)
                for i, v in enumerate(values)
            ]
        )
    )
    stats = rec.statistics("frequency_hz")
    assert stats.count == 2 and stats.mean == pytest.approx(2.0)
    assert rec.statistics("frequency_hz", 0.011, 0.031).count == 1


def test_statistics_of_an_empty_recording():
    stats = Recording().statistics("frequency_hz")
    assert stats.count == 0 and math.isnan(stats.mean)


def test_statistics_of_integer_columns():
    rec = Recording()
    rec.start(0.0)
    rec.append(batch_at(steady(0, 3)))
    assert rec.statistics("device_ms").maximum == 20.0


def test_append_performance_100k_samples_in_batches_of_5():
    rec = Recording()
    rec.start(0.0)
    batches = [make_batch(steady(i * 50, 5), host_time_s=[float(i)] * 5) for i in range(20_000)]
    started = time.perf_counter()
    for batch in batches:
        rec.append(batch)
    elapsed = time.perf_counter() - started
    assert len(rec) == 100_000
    assert elapsed < 1.0


# --- RollingBuffer ---------------------------------------------------------------------------


def rolling_batch(first: int, count: int) -> SampleBatch:
    return SampleBatch.from_samples(
        [
            make_sample(i, host_time_s=float(i), frequency_hz=float(i))
            for i in range(first, first + count)
        ]
    )


def test_rolling_buffer_keeps_the_newest_in_chronological_order():
    buf = RollingBuffer(5)
    assert len(buf) == 0 and buf.latest() is None
    buf.extend(rolling_batch(0, 3))
    assert buf.column("frequency_hz").tolist() == [0.0, 1.0, 2.0]
    buf.extend(rolling_batch(3, 4))
    assert len(buf) == 5
    assert buf.column("frequency_hz").tolist() == [2.0, 3.0, 4.0, 5.0, 6.0]
    assert buf.column("host_time_s").tolist() == [2.0, 3.0, 4.0, 5.0, 6.0]
    latest = buf.latest()
    assert latest is not None and latest["frequency_hz"] == 6.0
    assert set(CHANNELS) <= set(latest)


def test_rolling_buffer_batch_larger_than_capacity():
    buf = RollingBuffer(4)
    buf.extend(rolling_batch(0, 2))
    buf.extend(rolling_batch(10, 9))
    assert buf.column("frequency_hz").tolist() == [15.0, 16.0, 17.0, 18.0]


def test_rolling_buffer_many_small_batches_wrap_correctly():
    buf = RollingBuffer(7)
    for i in range(50):
        buf.extend(rolling_batch(i * 3, 3))
    assert buf.column("frequency_hz").tolist() == [float(v) for v in range(143, 150)]


def test_rolling_buffer_resize_keeps_the_newest():
    buf = RollingBuffer(6)
    buf.extend(rolling_batch(0, 9))  # wrapped
    buf.resize(3)
    assert buf.column("frequency_hz").tolist() == [6.0, 7.0, 8.0]
    buf.resize(10)
    assert buf.capacity == 10
    buf.extend(rolling_batch(9, 2))
    assert buf.column("frequency_hz").tolist() == [6.0, 7.0, 8.0, 9.0, 10.0]


def test_rolling_buffer_grows_on_demand_up_to_the_capacity():
    buf = RollingBuffer(100_000)
    assert buf._data.shape[1] < buf.capacity  # a large capacity is not allocated up front
    for i in range(30):
        buf.extend(rolling_batch(i * 1000, 1000))
    assert len(buf) == 30_000
    assert buf.column("frequency_hz").tolist() == [float(v) for v in range(30_000)]
    buf.resize(40_000)  # larger window: nothing is lost, the newest samples stay in order
    buf.extend(rolling_batch(30_000, 20_000))
    assert len(buf) == 40_000
    assert buf.column("frequency_hz").tolist() == [float(v) for v in range(10_000, 50_000)]


def test_rolling_buffer_clear_and_empty_batch():
    buf = RollingBuffer(3)
    buf.extend(rolling_batch(0, 3))
    buf.extend(SampleBatch.empty())
    assert len(buf) == 3
    buf.clear()
    assert len(buf) == 0 and buf.latest() is None
    assert buf.column("frequency_hz").shape == (0,)
