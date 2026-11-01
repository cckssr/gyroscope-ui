"""Device milliseconds to elapsed seconds, with reorder, restart and loss rules (PROTOCOL 4).

Rules, applied sample by sample in arrival order:

- the first sample after ``reset()`` defines the base (elapsed 0.0);
- a small backward step (at most ``restart_threshold_ms``) is a reordered datagram: the sample
  is dropped and counted;
- a larger backward step is a device restart or a uint32 wrap: a new segment starts whose
  elapsed time continues at ``last_elapsed + nominal period``; nothing is dropped (D4);
- a forward step longer than ``gap_factor`` times the nominal period is a gap: the missing
  samples are estimated and the gap is recorded;
- sequence numbers (protocol v2) give the exact loss between consecutive accepted samples.

A batch without anomalies takes a vectorised fast path; any anomaly falls back to the
per-sample rules for that batch.
"""

from __future__ import annotations

import statistics
from collections import deque

import numpy as np

from gyroscope_ui.core.models import NO_SEQ, Gap, RecordingQuality, SampleBatch

DEFAULT_PERIOD_S = 0.01
MIN_STEPS_FOR_GAPS = 3  # forward steps needed before the period estimate is trusted
_SEQ_MODULUS = 2**32
_SEQ_HALF = 2**31


class TimeBase:
    """Stateful converter of device time to recording time for one recording."""

    def __init__(
        self,
        restart_threshold_ms: int = 1000,
        gap_factor: float = 2.5,
        period_window: int = 50,
    ) -> None:
        self._restart_threshold_ms = restart_threshold_ms
        self._gap_factor = gap_factor
        self._period_window = period_window
        self._steps: deque[float] = deque(maxlen=period_window)
        self.reset()

    def reset(self) -> None:
        """Forget everything; the next sample defines a new base."""
        self._steps.clear()
        self._period_cache: float | None = None
        self._last_ms: int | None = None
        self._last_elapsed = 0.0
        self._segment_start_ms = 0
        self._segment_offset_s = 0.0
        self._last_seq: int | None = None
        self._reordered = 0
        self._restarts = 0
        self._lost_estimated = 0
        self._lost_exact: int | None = None
        self._gaps: list[Gap] = []

    @property
    def nominal_period_s(self) -> float:
        """Median of the recent positive time steps (``DEFAULT_PERIOD_S`` while unknown)."""
        if self._period_cache is None:
            if self._steps:
                self._period_cache = statistics.median(self._steps)
            else:
                self._period_cache = DEFAULT_PERIOD_S
        return self._period_cache

    def quality(self, samples: int) -> RecordingQuality:
        return RecordingQuality(
            samples=samples,
            reordered=self._reordered,
            lost_estimated=self._lost_estimated,
            lost_exact=self._lost_exact,
            restarts=self._restarts,
            gaps=tuple(self._gaps),
        )

    def process(self, batch: SampleBatch) -> tuple[np.ndarray, np.ndarray]:
        """Return ``(elapsed_s of the accepted samples, boolean accepted mask of the batch)``."""
        n = len(batch)
        accepted = np.ones(n, dtype=bool)
        if n == 0:
            return np.empty(0, dtype=np.float64), accepted
        fast = self._process_fast(batch.device_ms, batch.seq)
        if fast is not None:
            return fast, accepted
        elapsed: list[float] = []
        pairs = zip(batch.device_ms.tolist(), batch.seq.tolist(), strict=True)
        for i, (ms, seq) in enumerate(pairs):
            value = self._step(ms, seq)
            if value is None:
                accepted[i] = False
            else:
                elapsed.append(value)
        return np.array(elapsed, dtype=np.float64), accepted

    # --- fast path ---------------------------------------------------------------------------

    def _process_fast(self, ms: np.ndarray, seq: np.ndarray) -> np.ndarray | None:
        """Vectorised handling of a batch without anomalies, or ``None`` if there is one."""
        if self._last_ms is None or len(self._steps) < MIN_STEPS_FOR_GAPS:
            return None
        steps_ms = np.diff(ms, prepend=self._last_ms)
        if steps_ms.min() < 0:
            return None
        if (steps_ms / 1000.0 > self._gap_factor * self.nominal_period_s).any():
            return None
        has_seq = seq >= 0
        if has_seq.any():
            if not has_seq.all() or self._last_seq is None:
                return None
            seq_steps = np.diff(seq, prepend=self._last_seq) % _SEQ_MODULUS
            if (seq_steps != 1).any():
                return None
            self._last_seq = int(seq[-1])
        positive = steps_ms[steps_ms > 0]
        self._steps.extend((positive[-self._period_window :] / 1000.0).tolist())
        self._period_cache = None
        elapsed = self._segment_offset_s + (ms - self._segment_start_ms) / 1000.0
        self._last_ms = int(ms[-1])
        self._last_elapsed = float(elapsed[-1])
        return elapsed

    # --- per-sample path ---------------------------------------------------------------------

    def _step(self, ms: int, seq: int) -> float | None:
        restarted = self._last_ms is None
        if self._last_ms is None:
            self._segment_start_ms = ms
            self._segment_offset_s = 0.0
        else:
            delta_ms = ms - self._last_ms
            if delta_ms < 0:
                if -delta_ms <= self._restart_threshold_ms:
                    self._reordered += 1
                    return None
                self._restarts += 1
                self._segment_offset_s = self._last_elapsed + self.nominal_period_s
                self._segment_start_ms = ms
                restarted = True
            elif delta_ms > 0:
                self._note_step(delta_ms / 1000.0)
        elapsed = self._segment_offset_s + (ms - self._segment_start_ms) / 1000.0
        self._note_seq(seq, restarted)
        self._last_ms = ms
        self._last_elapsed = elapsed
        return elapsed

    def _note_step(self, step_s: float) -> None:
        period = self.nominal_period_s
        if len(self._steps) >= MIN_STEPS_FOR_GAPS and step_s > self._gap_factor * period:
            self._lost_estimated += max(0, round(step_s / period) - 1)
            self._gaps.append(Gap(start_s=self._last_elapsed, duration_s=step_s))
        self._steps.append(step_s)
        self._period_cache = None

    def _note_seq(self, seq: int, restarted: bool) -> None:
        if seq == NO_SEQ:
            return
        if self._lost_exact is None:
            self._lost_exact = 0
        if self._last_seq is not None and not restarted:
            missing = (seq - self._last_seq - 1) % _SEQ_MODULUS
            if missing < _SEQ_HALF:
                self._lost_exact += missing
        self._last_seq = seq
