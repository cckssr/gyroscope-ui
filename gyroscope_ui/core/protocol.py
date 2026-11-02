"""Line protocol of the Kreisel firmware (PROTOCOL.md sections 3, 5 and 6).

Parsing and validation only; sockets live in ``infrastructure``. ``parse_line`` raises
``LineError`` with a machine-readable ``reason``; ``parse_datagram`` never raises and counts
invalid lines instead.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from gyroscope_ui.core.models import Sample

UINT32_MAX = 2**32 - 1
_V1_FIELDS = 8
_V2_FIELDS = 9


@dataclass(frozen=True)
class Limits:
    """Plausibility bounds for the raw device values (generous, about 10x the sensor ranges)."""

    frequency_hz_max: float = 1000.0
    accel_m_s2_max: float = 200.0
    gyro_rad_s_max: float = 50.0


DEFAULT_LIMITS = Limits()


class LineError(ValueError):
    """A rejected data line; ``reason``: ``encoding``, ``field_count``, ``number`` or ``range``."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason


@dataclass(frozen=True)
class DatagramResult:
    """Outcome of one datagram: the valid samples, the invalid line count and the version seen."""

    samples: tuple[Sample, ...]
    invalid: int
    protocol_version: int | None  # from the last valid line: 8 fields -> 1, 9 fields -> 2


def _parse_uint(text: str) -> int:
    if not text.isascii() or not text.isdigit():
        raise LineError("number", text)
    value = int(text)
    if value > UINT32_MAX:
        raise LineError("range", text)
    return value


def _parse_float(text: str) -> float:
    if "_" in text:  # float() would accept "1_0"
        raise LineError("number", text)
    try:
        value = float(text)
    except ValueError:
        raise LineError("number", text) from None
    if not math.isfinite(value):
        raise LineError("number", text)
    return value


def parse_line(
    line: str,
    *,
    limits: Limits = DEFAULT_LIMITS,
    pulses_per_revolution: int = 1,
    host_time_s: float = 0.0,
) -> Sample:
    """Parse and validate one data line (8 fields = v1, 9 fields with ``seq`` = v2)."""
    if pulses_per_revolution < 1:
        raise ValueError("pulses_per_revolution must be >= 1")
    if not line.isascii():
        raise LineError("encoding")
    fields = [part.strip() for part in line.strip().split(",")]
    if len(fields) not in (_V1_FIELDS, _V2_FIELDS):
        raise LineError("field_count", str(len(fields)))

    device_ms = _parse_uint(fields[0])
    seq = _parse_uint(fields[8]) if len(fields) == _V2_FIELDS else None
    freq, ax, ay, az, gx, gy, gz = (_parse_float(f) for f in fields[1:8])

    if not 0.0 <= freq <= limits.frequency_hz_max:
        raise LineError("range", "frequency")
    if any(abs(a) > limits.accel_m_s2_max for a in (ax, ay, az)):
        raise LineError("range", "accel")
    if any(abs(g) > limits.gyro_rad_s_max for g in (gx, gy, gz)):
        raise LineError("range", "gyro")

    return Sample(
        device_ms=device_ms,
        frequency_hz=freq / pulses_per_revolution,
        accel_x_m_s2=ax,
        accel_y_m_s2=ay,
        accel_z_m_s2=az,
        gyro_x_rad_s=gx,
        gyro_y_rad_s=gy,
        gyro_z_rad_s=gz,
        seq=seq,
        host_time_s=host_time_s,
    )


def parse_datagram(
    payload: bytes,
    *,
    limits: Limits = DEFAULT_LIMITS,
    pulses_per_revolution: int = 1,
    host_time_s: float = 0.0,
) -> DatagramResult:
    """Parse all lines of one datagram; invalid lines are counted, blank lines ignored."""
    samples: list[Sample] = []
    invalid = 0
    version: int | None = None
    for raw in payload.split(b"\n"):
        try:
            text = raw.decode("ascii")
        except UnicodeDecodeError:
            invalid += 1
            continue
        if not text.strip():
            continue
        try:
            sample = parse_line(
                text,
                limits=limits,
                pulses_per_revolution=pulses_per_revolution,
                host_time_s=host_time_s,
            )
        except LineError:
            invalid += 1
            continue
        samples.append(sample)
        version = 1 if sample.seq is None else 2
    return DatagramResult(tuple(samples), invalid, version)


def registration_payload(host_ip: str, port: int) -> bytes:
    """Registration datagram sent to the device (also the keep-alive)."""
    return f"CONNECT:{host_ip}:{port}".encode("ascii")


def parse_host_port(text: str, default_port: int) -> tuple[str, int]:
    """Split ``host``, ``host:port``, ``[ipv6]`` or ``[ipv6]:port``; ValueError on a bad port."""
    text = text.strip()
    host, port_text = text, ""
    if text.startswith("["):
        end = text.find("]")
        if end < 0:
            raise ValueError("host: missing ']'")
        host, rest = text[1:end], text[end + 1 :]
        if rest:
            if not rest.startswith(":"):
                raise ValueError("host: unexpected text after ']'")
            port_text = rest[1:]
            if not port_text:
                raise ValueError("port: empty")
    elif text.count(":") == 1:
        host, port_text = text.split(":")
        if not port_text:
            raise ValueError("port: empty")
    if not host:
        raise ValueError("host: empty")
    if not port_text:
        return host, default_port
    if not port_text.isascii() or not port_text.isdigit():
        raise ValueError(f"port: {port_text!r}")
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise ValueError(f"port: {port}")
    return host, port


def parse_info(text: str) -> dict[str, str]:
    """Parse the ``Key: value`` lines of the HTTP ``/info`` body (HTTP header lines are skipped)."""
    result: dict[str, str] = {}
    for line in text.splitlines():
        key, sep, value = line.partition(":")
        key = key.strip()
        if sep and key:
            result[key] = value.strip()
    return result


def info_to_device_fields(info: dict[str, str]) -> tuple[str | None, str | None, int | None]:
    """``(device_id, firmware_version, protocol_version)`` from a ``parse_info`` result."""
    protocol: int | None = None
    raw = info.get("Protocol", "")
    if raw.isascii() and raw.isdigit():
        protocol = int(raw)
    return info.get("Device-ID") or None, info.get("Software-Version") or None, protocol
