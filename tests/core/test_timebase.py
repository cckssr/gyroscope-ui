from __future__ import annotations

import numpy as np
import pytest
from batches import make_batch, steady

from gyroscope_ui.core.models import Gap
from gyroscope_ui.core.timebase import TimeBase


def run(tb: TimeBase, device_ms, seq=None) -> tuple[np.ndarray, np.ndarray]:
    return tb.process(make_batch(device_ms, seq=seq))


def run_one_by_one(tb: TimeBase, device_ms, seq=None) -> list[float]:
    elapsed: list[float] = []
    for i, ms in enumerate(device_ms):
        e, mask = run(tb, [ms], None if seq is None else [seq[i]])
        elapsed.extend(e.tolist())
    return elapsed


def test_first_sample_defines_the_base():
    elapsed, mask = run(TimeBase(), [5000, 5010, 5020])
    assert mask.all()
    assert elapsed.tolist() == pytest.approx([0.0, 0.01, 0.02])


def test_empty_batch():
    elapsed, mask = run(TimeBase(), [])
    assert len(elapsed) == 0 and len(mask) == 0


def test_elapsed_continues_across_batches():
    tb = TimeBase()
    run(tb, steady(1000, 5))
    elapsed, _ = run(tb, steady(1050, 5))
    assert elapsed.tolist() == pytest.approx([0.05, 0.06, 0.07, 0.08, 0.09])


def test_reorder_is_dropped_and_counted():
    tb = TimeBase()
    ms = [*steady(0, 6), 25, *steady(60, 3)]  # the 25 arrives late
    elapsed, mask = run(tb, ms)
    assert mask.tolist() == [True] * 6 + [False] + [True] * 3
    assert len(elapsed) == 9
    assert elapsed.tolist() == pytest.approx([0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08])
    quality = tb.quality(9)
    assert quality.reordered == 1 and quality.restarts == 0


def test_reorder_at_exactly_the_threshold_is_not_a_restart():
    tb = TimeBase(restart_threshold_ms=1000)
    _, mask = run(tb, [5000, 5010, 4010, 5020])
    assert mask.tolist() == [True, True, False, True]
    assert tb.quality(3).restarts == 0


def test_restart_continues_with_the_nominal_period_and_drops_nothing():
    tb = TimeBase()
    elapsed, mask = run(tb, [*steady(0, 300), *steady(0, 5)])  # reboot after 3 s of uptime
    assert mask.all() and len(elapsed) == 305
    assert elapsed[299] == pytest.approx(2.99)
    assert elapsed[300] == pytest.approx(3.00)  # last + nominal period
    assert elapsed[304] == pytest.approx(3.04)
    assert np.all(np.diff(elapsed) > 0)
    quality = tb.quality(305)
    assert quality.restarts == 1 and quality.reordered == 0


def test_uint32_millis_wrap_is_handled_as_a_restart():
    tb = TimeBase()
    top = 2**32
    ms = [top - 30, top - 20, top - 10, 0, 10, 20]  # millis() wraps to 0
    elapsed, mask = run(tb, ms)
    assert mask.all()
    assert elapsed.tolist() == pytest.approx([0.0, 0.01, 0.02, 0.03, 0.04, 0.05])
    assert tb.quality(6).restarts == 1


def test_gap_counts_estimated_loss_and_records_the_gap():
    tb = TimeBase()
    ms = [*steady(0, 10), 190, 200]  # last regular sample at 90 ms, next at 190 ms
    elapsed, mask = run(tb, ms)
    assert mask.all()
    quality = tb.quality(12)
    assert quality.lost_estimated == 9
    assert quality.gaps == (Gap(start_s=pytest.approx(0.09), duration_s=pytest.approx(0.1)),)
    assert elapsed[10] == pytest.approx(0.19)


def test_gap_in_a_later_batch_equals_the_gap_in_one_batch():
    ms = [*steady(0, 10), 190, 200]
    a, b = TimeBase(), TimeBase()
    run(a, ms)
    run(b, ms[:10])
    run(b, ms[10:])
    assert a.quality(12) == b.quality(12)


def test_small_jitter_is_not_a_gap():
    tb = TimeBase()
    ms = np.cumsum([0, 10, 12, 8, 14, 9, 11, 10, 24, 10, 10]).tolist()
    run(tb, ms)
    quality = tb.quality(len(ms))
    assert quality.lost_estimated == 0 and quality.gaps == ()


def test_no_gap_is_reported_before_the_period_is_known():
    tb = TimeBase()
    run(tb, [0, 100, 200])  # a slow device: period 0.1 s is not a gap
    assert tb.quality(3).gaps == ()
    assert tb.nominal_period_s == pytest.approx(0.1)


def test_nominal_period_is_the_median_and_defaults_to_ten_ms():
    tb = TimeBase()
    assert tb.nominal_period_s == 0.01
    run(tb, [0, 10, 20, 30, 80, 90, 100])
    assert tb.nominal_period_s == pytest.approx(0.01)


def test_exact_loss_from_sequence_numbers():
    tb = TimeBase()
    run(tb, steady(0, 6), seq=[0, 1, 2, 5, 6, 8])
    assert tb.quality(6).lost_exact == 3  # 3 and 4, then 7


def test_sequence_loss_across_the_uint32_wrap():
    tb = TimeBase()
    top = 2**32
    run(tb, steady(0, 6), seq=[top - 3, top - 2, top - 1, 0, 1, 3])
    assert tb.quality(6).lost_exact == 1  # only 2 is missing


def test_sequence_loss_wrap_with_missing_samples_around_it():
    tb = TimeBase()
    run(tb, steady(0, 3), seq=[2**32 - 2, 1, 2])  # lost: 2**32-1 and 0
    assert tb.quality(3).lost_exact == 2


def test_lost_exact_is_none_without_sequence_numbers_and_zero_with_a_clean_run():
    tb = TimeBase()
    run(tb, steady(0, 5))
    assert tb.quality(5).lost_exact is None
    tb.reset()
    run(tb, steady(0, 5), seq=[10, 11, 12, 13, 14])
    assert tb.quality(5).lost_exact == 0


def test_sequence_restart_with_the_clock_does_not_count_loss():
    tb = TimeBase()
    run(tb, [*steady(0, 300), *steady(0, 3)], seq=[*range(5000, 5300), 0, 1, 2])
    assert tb.quality(303).lost_exact == 0
    assert tb.quality(303).restarts == 1


def test_sequence_going_backwards_counts_no_loss():
    tb = TimeBase()
    run(tb, steady(0, 4), seq=[10, 11, 5, 6])
    assert tb.quality(4).lost_exact == 0


def test_batch_and_per_sample_processing_agree():
    rng = np.random.default_rng(7)
    steps = rng.integers(8, 13, size=400)
    ms = np.cumsum(steps).tolist()
    ms[200:200] = [ms[199] + 400]  # one gap
    seq = list(range(len(ms)))
    a, b = TimeBase(), TimeBase()
    batch_elapsed, _ = run(a, ms, seq)
    single_elapsed = run_one_by_one(b, ms, seq)
    assert batch_elapsed.tolist() == pytest.approx(single_elapsed)
    assert a.quality(len(ms)) == b.quality(len(ms))


def test_reset_forgets_everything():
    tb = TimeBase()
    run(tb, [*steady(0, 300), *steady(0, 3)])
    tb.reset()
    elapsed, _ = run(tb, [777, 787])
    assert elapsed.tolist() == pytest.approx([0.0, 0.01])
    quality = tb.quality(2)
    assert quality.restarts == 0 and quality.reordered == 0 and quality.gaps == ()
