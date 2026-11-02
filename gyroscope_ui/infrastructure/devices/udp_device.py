"""UDP adapter for the Kreisel firmware (PROTOCOL.md sections 2 to 5).

The host binds the local port the firmware sends to (no fallback port, D6), registers with a
``CONNECT:<ip>:<port>`` datagram and repeats it as keep-alive. Parsing and validation live in
``core.protocol``; this class only moves bytes.
"""

from __future__ import annotations

import contextlib
import dataclasses
import errno
import http.client
import socket
import sys
import time
from collections.abc import Callable

from gyroscope_ui.core import protocol
from gyroscope_ui.core.models import DeviceInfo, LinkStats, Sample
from gyroscope_ui.core.protocol import Limits
from gyroscope_ui.infrastructure.devices.base import (
    DeviceError,
    DevicePortInUseError,
    LinkMeter,
)
from gyroscope_ui.infrastructure.logging import get_logger

_log = get_logger("udp")

_PORT_IN_USE_ERRNOS = {errno.EADDRINUSE, errno.EACCES}
_WINERROR_PORT_IN_USE = {10048, 10013}  # WSAEADDRINUSE, WSAEACCES (SO_EXCLUSIVEADDRUSE)
_WSAEMSGSIZE = 10040
_MAX_DATAGRAM_BYTES = 4096
_INFO_ATTEMPTS = 4  # ``GET /info`` tries per connection (see ``_fetch_info``)
_INFO_RETRY_DELAY_S = 0.15
_MAX_DRAIN = 2000  # datagrams per read(): bounds the call even if the sender is faster than us


def _is_port_in_use(exc: OSError) -> bool:
    codes = (exc.errno, getattr(exc, "winerror", None))
    return bool(set(codes) & (_PORT_IN_USE_ERRNOS | _WINERROR_PORT_IN_USE))


def _local_ip_towards(host_ip: str, port: int) -> str:
    """Address of the interface that routes to the device (nothing is sent); ``0.0.0.0`` if
    it cannot be determined."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect((host_ip, port))
            return str(probe.getsockname()[0])
    except OSError as exc:
        _log.debug("cannot determine the local address towards %s: %s", host_ip, exc)
        return "0.0.0.0"


class UdpGyroDevice:
    """The real Kreisel: UDP data on ``local_port``, optional HTTP ``/info`` on ``http_port``."""

    def __init__(
        self,
        host: str,
        port: int = 12345,
        local_port: int = 12345,
        *,
        http_port: int = 80,
        info_timeout_s: float = 1.0,
        limits: Limits | None = None,
        pulses_per_revolution: int = 1,
        bind_host: str = "0.0.0.0",
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.host = host
        self.port = port
        self.local_port = local_port
        self.http_port = http_port
        self._info_timeout_s = info_timeout_s
        self._limits = limits if limits is not None else Limits()
        self._pulses = pulses_per_revolution
        self._bind_host = bind_host
        self._clock = clock
        self._meter = LinkMeter(clock)
        self._sock: socket.socket | None = None
        self._host_ip = ""
        self._registration = b""
        self._info = DeviceInfo(host, f"{host}:{port}")
        self._data_protocol: int | None = None
        self.foreign_datagrams = 0  # debug counter: datagrams from other sources (ignored)

    # ---- GyroDevice ---------------------------------------------------------------------
    @property
    def info(self) -> DeviceInfo:
        return self._info

    @property
    def is_open(self) -> bool:
        return self._sock is not None

    def open(self) -> None:
        if self._sock is not None:
            return
        try:
            self._host_ip = socket.gethostbyname(self.host)
        except OSError as exc:
            raise DeviceError("device_open_failed", error=str(exc)) from exc
        self._sock = self._bind()
        self._meter.reset()
        self._info = DeviceInfo(self.host, f"{self.host}:{self.port}")
        self._data_protocol = None
        self.foreign_datagrams = 0
        local_ip = _local_ip_towards(self._host_ip, self.port)
        self._registration = protocol.registration_payload(local_ip, self.local_port)
        self._register()
        self._fetch_info()

    def close(self) -> None:
        sock, self._sock = self._sock, None
        if sock is not None:
            with contextlib.suppress(OSError):
                sock.close()

    def read(self, timeout_s: float) -> list[Sample]:
        sock = self._sock
        if sock is None:
            return []
        samples: list[Sample] = []
        wait_s = max(timeout_s, 0.0)
        try:
            for _ in range(_MAX_DRAIN):
                try:
                    sock.settimeout(wait_s)
                    payload, addr = sock.recvfrom(_MAX_DATAGRAM_BYTES)
                except (TimeoutError, BlockingIOError):
                    break
                except (ConnectionResetError, ConnectionRefusedError):
                    continue  # ICMP "port unreachable" echo of a keep-alive (Windows, Linux)
                except OSError as exc:
                    if getattr(exc, "winerror", None) != _WSAEMSGSIZE:
                        raise
                    self._meter.add(0, 1)  # oversized datagram (Windows raises, POSIX truncates)
                    continue
                wait_s = 0.0  # after the first datagram only drain what is already queued
                self._handle(payload, addr[0], samples)
        except OSError as exc:
            if self._sock is not sock:  # closed while waiting
                return samples
            raise DeviceError("device_io_failed", error=str(exc)) from exc
        return samples

    def keepalive(self) -> None:
        if self._sock is not None:
            self._register()

    def stats(self) -> LinkStats:
        version = self._data_protocol or self._info.protocol_version
        return self._meter.snapshot(version)

    # ---- internals ----------------------------------------------------------------------
    def _bind(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            if sys.platform == "win32":
                if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                if hasattr(socket, "SIO_UDP_CONNRESET"):
                    sock.ioctl(socket.SIO_UDP_CONNRESET, False)  # type: ignore[attr-defined]
            sock.bind((self._bind_host, self.local_port))
        except OSError as exc:
            sock.close()
            if _is_port_in_use(exc):
                raise DevicePortInUseError(port=self.local_port) from exc
            raise DeviceError("device_open_failed", error=str(exc)) from exc
        return sock

    def _register(self) -> None:
        """Send the registration; failures are not fatal (the next keep-alive retries)."""
        sock = self._sock
        if sock is None:
            return
        try:
            sock.sendto(self._registration, (self._host_ip, self.port))
        except OSError as exc:
            _log.debug("registration with %s:%s failed: %s", self._host_ip, self.port, exc)

    def _handle(self, payload: bytes, source_ip: str, out: list[Sample]) -> None:
        if source_ip != self._host_ip:
            self.foreign_datagrams += 1
            return
        result = protocol.parse_datagram(
            payload,
            limits=self._limits,
            pulses_per_revolution=self._pulses,
            host_time_s=self._clock(),
        )
        self._meter.add(len(result.samples), result.invalid)
        out.extend(result.samples)
        if result.protocol_version is not None:
            self._data_protocol = result.protocol_version
            if self._info.protocol_version is None:
                self._info = dataclasses.replace(
                    self._info, protocol_version=result.protocol_version
                )

    def _fetch_info(self) -> None:
        """``GET /info`` (best effort): device ID, firmware and protocol version.

        The firmware serves HTTP from its main loop and drops a connection whose request has not
        arrived yet, so a single attempt fails now and then: try a few times."""
        body = None
        for attempt in range(_INFO_ATTEMPTS):
            if attempt:
                time.sleep(_INFO_RETRY_DELAY_S)
            try:
                body = self._get_info()
                break
            except (OSError, http.client.HTTPException) as exc:
                _log.debug(
                    "no device information from %s:%s (attempt %d): %s",
                    self.host,
                    self.http_port,
                    attempt + 1,
                    exc,
                )
        if body is None:
            _log.warning("no device information from %s:%s", self.host, self.http_port)
            return
        device_id, firmware, version = protocol.info_to_device_fields(protocol.parse_info(body))
        self._info = DeviceInfo(
            device_id or self.host,
            f"{self.host}:{self.port}",
            simulated=False,
            firmware_version=firmware,
            protocol_version=version,
        )

    def _get_info(self) -> str:
        conn = http.client.HTTPConnection(self._host_ip, self.http_port, self._info_timeout_s)
        try:
            conn.request("GET", "/info")
            response = conn.getresponse()
            if response.status != 200:
                raise http.client.HTTPException(f"status {response.status}")
            return response.read(_MAX_DATAGRAM_BYTES * 4).decode("utf-8", errors="replace")
        finally:
            conn.close()
