"""Simulated Kreisel behind the ``GyroDevice`` protocol (``--simulate`` and the tests).

Samples come from ``core.simulation``: sample ``k`` is due at simulated time ``k / rate_hz``,
and simulated time runs ``1 / time_scale`` times faster than the host clock (``time_scale``
0.01 = 100x). ``read`` hands out everything that is due, at most ``max_batch`` per call, so a
slow reader catches up over several calls. Commands (``kick``, ``pause_stream``,
``fail_next_read``) are thread-safe.
"""

from __future__ import annotations

import dataclasses
import threading
import time
from collections.abc import Callable

from gyroscope_ui.core.models import DeviceInfo, LinkStats, Sample
from gyroscope_ui.core.simulation import GyroSimulation, SimulationParams
from gyroscope_ui.infrastructure.devices.base import DeviceError, LinkMeter

_SEQ_WRAP = 2**32


class MockGyroscope:
    """Device ID ``SIM0001``; deterministic for a given ``SimulationParams.seed``."""

    def __init__(
        self,
        params: SimulationParams | None = None,
        *,
        time_scale: float = 1.0,
        max_batch: int = 500,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if time_scale <= 0.0:
            raise ValueError("time_scale must be > 0")
        self.params = params if params is not None else SimulationParams()
        self.time_scale = time_scale
        self.max_batch = max(1, max_batch)
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._meter = LinkMeter(clock)
        self._sim = GyroSimulation(self.params)
        self._open = False
        self._t_open_s = 0.0
        self._next_index = 0
        self._seq = 0
        self._paused = False
        self._fail_key: str | None = None
        self._info = DeviceInfo(
            "SIM0001",
            "simulation",
            simulated=True,
            firmware_version="sim",
            protocol_version=self.params.protocol_version,
        )

    # ---- GyroDevice ---------------------------------------------------------------------
    @property
    def info(self) -> DeviceInfo:
        return self._info

    @property
    def is_open(self) -> bool:
        return self._open

    def open(self) -> None:
        with self._lock:
            if self._open:
                return
            self._sim = GyroSimulation(self.params)
            self._t_open_s = self._clock()
            self._next_index = 0
            self._seq = 0
            self._paused = False
            self._fail_key = None
            self._meter.reset()
            self._open = True

    def close(self) -> None:
        with self._lock:
            self._open = False

    def read(self, timeout_s: float) -> list[Sample]:
        samples = self._take_due()
        if not samples and self.is_open:
            # nothing due: wait for about one sample period (never longer than the timeout)
            self._sleep(max(0.0, min(timeout_s, self.time_scale / self.params.rate_hz)))
            samples = self._take_due()
        return samples

    def keepalive(self) -> None:
        """Nothing to refresh."""

    def stats(self) -> LinkStats:
        return self._meter.snapshot(self.params.protocol_version)

    # ---- simulation commands (thread-safe) ----------------------------------------------
    def kick(self, frequency_hz: float | None = None) -> None:
        """Spin the disc up again (default: the configured start frequency)."""
        with self._lock:
            if self._open:
                self._sim.kick(self._sim_time_s(), frequency_hz)

    def pause_stream(self, paused: bool) -> None:
        """No samples while paused (emulates a silent device); they are not caught up later."""
        with self._lock:
            self._paused = paused

    def fail_next_read(self, key: str = "device_io_failed") -> None:
        """The next ``read`` raises ``DeviceError(key)``."""
        with self._lock:
            self._fail_key = key

    # ---- internals ----------------------------------------------------------------------
    def _sim_time_s(self) -> float:
        return (self._clock() - self._t_open_s) / self.time_scale

    def _take_due(self) -> list[Sample]:
        with self._lock:
            if self._fail_key is not None:
                key, self._fail_key = self._fail_key, None
                raise DeviceError(key, error="simulated failure")
            if not self._open:
                return []
            rate_hz = self.params.rate_hz
            last_due = int(self._sim_time_s() * rate_hz + 1e-9)
            if self._paused:
                self._next_index = max(self._next_index, last_due + 1)
                return []
            stop = min(last_due, self._next_index + self.max_batch - 1)
            v2 = self.params.protocol_version == 2
            samples: list[Sample] = []
            for index in range(self._next_index, stop + 1):
                seq = self._seq
                self._seq = (self._seq + 1) % _SEQ_WRAP
                if self._sim.should_drop(index):
                    continue
                t_s = index / rate_hz
                sample = self._sim.sample_at(t_s, seq if v2 else None)
                host_time_s = self._t_open_s + t_s * self.time_scale
                samples.append(dataclasses.replace(sample, host_time_s=host_time_s))
            self._next_index = stop + 1
        self._meter.add(len(samples))
        return samples
