from __future__ import annotations

import math

import pytest

from gyroscope_ui.core.protocol import (
    Limits,
    LineError,
    info_to_device_fields,
    parse_datagram,
    parse_host_port,
    parse_info,
    parse_line,
    registration_payload,
)

V1 = "123456,14.9876,0.1000,-0.2000,9.8100,0.0100,-0.0200,2.1000\r\n"


def test_parse_v1_line():
    s = parse_line(V1, host_time_s=7.5)
    assert s.device_ms == 123456
    assert s.frequency_hz == pytest.approx(14.9876)
    assert (s.accel_x_m_s2, s.accel_y_m_s2, s.accel_z_m_s2) == (0.1, -0.2, 9.81)
    assert (s.gyro_x_rad_s, s.gyro_y_rad_s, s.gyro_z_rad_s) == (0.01, -0.02, 2.1)
    assert s.seq is None and s.host_time_s == 7.5


def test_parse_v2_line_has_sequence_number():
    s = parse_line(V1.strip() + ",4294967295\r\n")
    assert s.seq == 4294967295


@pytest.mark.parametrize("device_ms", [2000000, 1111111, 4294967295, 0])
def test_d7_lines_with_repeated_digits_are_valid(device_ms):
    """D7: the old 'six identical characters' rule rejected these valid lines."""
    s = parse_line(f"{device_ms},0.0000,0.0000,0.0000,0.0000,0.0000,0.0000,0.0000")
    assert s.device_ms == device_ms


def test_pulses_per_revolution_divides_the_raw_frequency():
    assert parse_line(V1, pulses_per_revolution=2).frequency_hz == pytest.approx(14.9876 / 2)


def test_range_check_applies_to_the_raw_frequency():
    line = "1,900.0000,0,0,0,0,0,0"
    assert parse_line(line, pulses_per_revolution=2).frequency_hz == 450.0
    with pytest.raises(LineError) as err:
        parse_line("1,1001.0000,0,0,0,0,0,0", pulses_per_revolution=10)
    assert err.value.reason == "range"


@pytest.mark.parametrize(
    ("line", "reason"),
    [
        ("1,2,3", "field_count"),
        ("", "field_count"),
        ("1,2,3,4,5,6,7,8,9,10", "field_count"),
        ("1,0,0,0,0,0,0,0ä", "encoding"),
        ("-1,0,0,0,0,0,0,0", "number"),
        ("1.5,0,0,0,0,0,0,0", "number"),
        ("1,nan,0,0,0,0,0,0", "number"),
        ("1,inf,0,0,0,0,0,0", "number"),
        ("1,1_0,0,0,0,0,0,0", "number"),
        ("1,abc,0,0,0,0,0,0", "number"),
        ("1,0,0,0,0,0,0,0,-3", "number"),
        ("4294967296,0,0,0,0,0,0,0", "range"),
        ("1,-0.1,0,0,0,0,0,0", "range"),
        ("1,0,200.1,0,0,0,0,0", "range"),
        ("1,0,0,0,-200.1,0,0,0", "range"),
        ("1,0,0,0,0,50.1,0,0", "range"),
        ("1,0,0,0,0,0,0,-50.1", "range"),
    ],
)
def test_invalid_lines_carry_a_reason(line, reason):
    with pytest.raises(LineError) as err:
        parse_line(line)
    assert err.value.reason == reason
    assert isinstance(err.value, ValueError)


def test_custom_limits():
    limits = Limits(frequency_hz_max=10.0, accel_m_s2_max=1.0, gyro_rad_s_max=1.0)
    with pytest.raises(LineError):
        parse_line(V1, limits=limits)


def test_datagram_mixed_valid_invalid_and_non_ascii():
    payload = (
        V1.encode()
        + b"garbage\r\n"
        + b"\r\n"
        + b"7,1.0000,0,0,0,0,0,0,3\r\n"
        + "1,ä,0,0,0,0,0,0\r\n".encode()
        + b"\xff\xfe,1,2\n"
        + b"   \n"
    )
    result = parse_datagram(payload, host_time_s=2.0)
    assert [s.device_ms for s in result.samples] == [123456, 7]
    assert all(s.host_time_s == 2.0 for s in result.samples)
    assert result.invalid == 3
    assert result.protocol_version == 2  # from the last valid line (9 fields)


def test_datagram_version_and_empty_payloads():
    assert parse_datagram(V1.encode()).protocol_version == 1
    for payload in (b"", b"\r\n", b"\x00\x01"):
        result = parse_datagram(payload)
        assert result.samples == () and result.protocol_version is None
    assert parse_datagram(b"\x00\x01").invalid == 1


def test_datagram_never_raises_on_binary_noise():
    for payload in (bytes(range(256)), b"," * 50, b"1," * 100):
        assert parse_datagram(payload).samples == ()


def test_datagram_applies_pulses_per_revolution():
    result = parse_datagram(V1.encode(), pulses_per_revolution=2)
    assert result.samples[0].frequency_hz == pytest.approx(14.9876 / 2)


def test_registration_payload():
    assert registration_payload("192.168.4.2", 12345) == b"CONNECT:192.168.4.2:12345"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("192.168.4.1:12345", ("192.168.4.1", 12345)),
        ("192.168.4.1", ("192.168.4.1", 99)),
        (" kreisel.local ", ("kreisel.local", 99)),
        ("[::1]:5", ("::1", 5)),
        ("[::1]", ("::1", 99)),
        ("::1", ("::1", 99)),
    ],
)
def test_parse_host_port(text, expected):
    assert parse_host_port(text, 99) == expected


@pytest.mark.parametrize(
    "text", ["host:abc", "host:", "host:0", "host:70000", ":80", "[::1", "[::1]x", ""]
)
def test_parse_host_port_rejects_bad_input(text):
    with pytest.raises(ValueError):
        parse_host_port(text, 99)


def test_parse_info_and_device_fields():
    body = (
        "Device-ID: E35433\nSoftware-Version: 1.1.1\nUptime: 5000 ms\n"
        "IP-Adresse: 192.168.4.1\nProtocol: 2\nno colon here\n"
    )
    info = parse_info(body)
    assert info["Device-ID"] == "E35433"
    assert info["IP-Adresse"] == "192.168.4.1"
    assert "no colon here" not in info
    assert info_to_device_fields(info) == ("E35433", "1.1.1", 2)


def test_device_fields_of_a_v1_device_or_garbage():
    assert info_to_device_fields(parse_info("Device-ID: E1\nSoftware-Version: 1.1.1\n")) == (
        "E1",
        "1.1.1",
        None,
    )
    assert info_to_device_fields({"Protocol": "x"}) == (None, None, None)
    assert info_to_device_fields({}) == (None, None, None)


def test_parse_line_values_are_finite_floats():
    s = parse_line(V1)
    assert all(math.isfinite(v) for v in (s.frequency_hz, s.gyro_z_rad_s))
