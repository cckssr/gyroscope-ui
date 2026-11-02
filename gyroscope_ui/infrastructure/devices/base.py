"""Device interface implemented by the UDP adapter and the mock, plus shared helpers."""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

from gyroscope_ui.core.models import DeviceInfo, LinkStats, Sample


class DeviceError(RuntimeError):
    """Device failure carrying a message key (``config.json`` "messages") and format args.

    ``str(exc)`` is the key plus the args, suitable for logs; the UI shows the translated
    message via ``AppConfig.message(exc.key, **exc.fmt)``.
    """

    default_key = "device_error"

    def __init__(self, key: str | None = None, **fmt: Any) -> None:
        self.key = key or self.default_key
        self.fmt = fmt
        detail = ", ".join(f"{k}={v}" for k, v in fmt.items())
        super().__init__(f"{self.key}: {detail}" if detail else self.key)


class DeviceTimeoutError(DeviceError):
    """The device did not answer in time."""

    default_key = "device_timeout"


class DevicePortInUseError(DeviceError):
    """The local UDP port is taken (a second instance of the application, another program)."""

    default_key = "device_port_in_use"


@runtime_checkable
class GyroDevice(Protocol):
    """Gyroscope adapter (real or simulated).

    After ``open()`` only one thread (the acquisition worker) calls ``read``, ``keepalive`` and
    ``stats``. Failures raise :class:`DeviceError` (or a subclass).
    """

    @property
    def info(self) -> DeviceInfo:
        """Identity of the device; refined by ``open()`` (``/info``) and by the received data."""
        ...

    @property
    def is_open(self) -> bool: ...

    def open(self) -> None:
        """Bind, register and read the device information (best effort)."""
        ...

    def close(self) -> None:
        """Release the socket; safe to call more than once."""
        ...

    def read(self, timeout_s: float) -> list[Sample]:
        """Valid samples received; waits up to ``timeout_s`` for the first datagram (may be [])."""
        ...

    def keepalive(self) -> None:
        """Re-send the registration (a no-op for the mock)."""
        ...

    def stats(self) -> LinkStats:
        """Counters since ``open()``."""
        ...


class LinkMeter:
    """Counters behind ``LinkStats``: totals, a sliding-window sample rate and the data age."""

    def __init__(self, clock: Callable[[], float] = time.monotonic, window_s: float = 2.0) -> None:
        self._clock = clock
        self._window_s = window_s
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._start_s = self._clock()
            self._window: deque[tuple[float, int]] = deque()
            self._received = 0
            self._invalid = 0
            self._last_valid_s: float | None = None

    def add(self, valid: int, invalid: int = 0) -> None:
        """Count the outcome of one read (valid samples and rejected lines)."""
        now = self._clock()
        with self._lock:
            self._invalid += invalid
            if valid:
                self._received += valid
                self._window.append((now, valid))
                self._last_valid_s = now

    def snapshot(self, protocol_version: int | None = None) -> LinkStats:
        now = self._clock()
        with self._lock:
            while self._window and now - self._window[0][0] > self._window_s:
                self._window.popleft()
            span_s = min(self._window_s, max(now - self._start_s, 0.5))
            rate_hz = sum(n for _t, n in self._window) / span_s
            age_s = None if self._last_valid_s is None else now - self._last_valid_s
            return LinkStats(rate_hz, self._received, self._invalid, age_s, protocol_version)
