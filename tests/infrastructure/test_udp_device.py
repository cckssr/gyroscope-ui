"""UdpGyroDevice against the loopback fake firmware (never the real port 12345)."""

from __future__ import annotations

import socket
import time

import pytest
from fake_firmware import LOCALHOST, FakeFirmware, free_udp_port

from gyroscope_ui.core.models import LinkStats
from gyroscope_ui.infrastructure.devices.base import (
    DeviceError,
    DevicePortInUseError,
    GyroDevice,
)
from gyroscope_ui.infrastructure.devices.udp_device import UdpGyroDevice


def make_device(firmware: FakeFirmware, local_port: int, **kwargs) -> UdpGyroDevice:
    kwargs.setdefault("http_port", firmware.http_port or free_udp_port())
    kwargs.setdefault("info_timeout_s", 0.5)
    return UdpGyroDevice(LOCALHOST, firmware.port, local_port, bind_host=LOCALHOST, **kwargs)


def read_until(device, count: int, timeout_s: float = 5.0) -> list:
    """Read until at least ``count`` samples arrived."""
    samples: list = []
    deadline = time.monotonic() + timeout_s
    while len(samples) < count and time.monotonic() < deadline:
        samples.extend(device.read(0.05))
    return samples


@pytest.fixture
def device(firmware, local_port):
    dev = make_device(firmware, local_port)
    dev.open()
    yield dev
    dev.close()


def test_is_a_gyro_device(firmware, local_port):
    assert isinstance(make_device(firmware, local_port), GyroDevice)


def test_open_registers_and_reads_v1_lines(firmware, device):
    assert device.is_open
    assert firmware.wait_for_registrations(1)
    samples = read_until(device, 20)
    assert len(samples) >= 20
    assert all(s.seq is None for s in samples)
    times = [s.device_ms for s in samples]
    assert times == sorted(times)
    assert all(s.host_time_s > 0 for s in samples)
    stats = device.stats()
    assert isinstance(stats, LinkStats)
    assert stats.received >= 20 and stats.invalid == 0
    assert stats.rate_hz > 0 and stats.data_age_s is not None and stats.data_age_s < 2.0


def test_v2_lines_carry_sequence_numbers_and_the_protocol_version(local_port):
    with FakeFirmware(protocol_version=2, data_port=local_port) as fake:
        dev = make_device(fake, local_port)
        dev.open()
        try:
            assert dev.info.protocol_version == 2  # from /info
            samples = read_until(dev, 20)
            seqs = [s.seq for s in samples]
            assert None not in seqs
            assert seqs == list(range(seqs[0], seqs[0] + len(seqs)))
            assert dev.stats().protocol_version == 2
        finally:
            dev.close()


def test_info_is_fetched_again_when_the_first_requests_are_dropped(local_port):
    with FakeFirmware(protocol_version=2, data_port=local_port, device_id="E94464") as fake:
        fake.drop_http_requests = 2
        dev = make_device(fake, local_port)
        dev.open()
        try:
            assert dev.info.device_id == "E94464"
            assert dev.info.firmware_version == fake.software_version
        finally:
            dev.close()


def test_v2_registration_payload_selects_the_data_port(local_port):
    # the fake sends to the port in the CONNECT payload, not to ``data_port``
    with FakeFirmware(protocol_version=2, data_port=1, http=False) as fake:
        dev = make_device(fake, local_port)
        dev.open()
        try:
            assert len(read_until(dev, 5)) >= 5
        finally:
            dev.close()


def test_protocol_version_is_learned_from_the_data_without_http(local_port):
    with FakeFirmware(protocol_version=2, data_port=local_port, http=False) as fake:
        dev = make_device(fake, local_port)
        dev.open()
        try:
            assert dev.info.protocol_version is None
            read_until(dev, 5)
            assert dev.info.protocol_version == 2
            assert dev.stats().protocol_version == 2
        finally:
            dev.close()


def test_info_fills_the_device_info(firmware, device):
    info = device.info
    assert info.device_id == "E35433"
    assert info.firmware_version == "1.1.1"
    assert info.address == f"{LOCALHOST}:{firmware.port}"
    assert not info.simulated
    assert info.protocol_version is None  # firmware v1 does not report one
    read_until(device, 5)
    assert device.info.protocol_version == 1


def test_missing_http_server_keeps_the_defaults(local_port):
    with FakeFirmware(data_port=local_port, http=False) as fake:
        dev = UdpGyroDevice(
            LOCALHOST,
            fake.port,
            local_port,
            http_port=free_udp_port(),
            info_timeout_s=0.2,
            bind_host=LOCALHOST,
        )
        dev.open()
        try:
            assert dev.is_open
            assert dev.info.device_id == LOCALHOST
            assert dev.info.firmware_version is None
            assert len(read_until(dev, 3)) >= 3
        finally:
            dev.close()


def test_garbage_and_non_ascii_are_counted_invalid(firmware, device):
    assert firmware.wait_for_registrations(1)
    firmware.stop_sending()
    device.read(0.2)  # drain what is in flight
    before = device.stats()
    firmware.send_raw(b"hello world\r\n")
    firmware.send_raw("1,2,3,4,5,6,7,Ä\r\n".encode())
    firmware.send_raw(b"\xff\xfe\x00")
    deadline = time.monotonic() + 3.0
    while device.stats().invalid - before.invalid < 3 and time.monotonic() < deadline:
        assert device.read(0.05) == []
    after = device.stats()
    assert after.invalid - before.invalid == 3
    assert after.received == before.received


def test_datagrams_from_a_foreign_source_are_ignored(firmware, device, local_port):
    foreign = _foreign_socket()
    if foreign is None:
        pytest.skip("no second local address available")
    with foreign:
        assert firmware.wait_for_registrations(1)
        firmware.stop_sending()
        device.read(0.2)
        before = device.stats().received
        line = firmware._sim.line_at(1.0).encode()
        foreign.sendto(line, (LOCALHOST, local_port))
        deadline = time.monotonic() + 3.0
        while device.foreign_datagrams == 0 and time.monotonic() < deadline:
            assert device.read(0.05) == []
        if device.foreign_datagrams == 0:
            pytest.skip("the datagram did not arrive with a foreign source address")
        assert device.stats().received == before


def _foreign_socket() -> socket.socket | None:
    """A UDP socket whose source address differs from 127.0.0.1 (None if there is none)."""
    candidates = ["127.0.0.2"]
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("192.0.2.1", 9))  # nothing is sent; selects the outgoing interface
            candidates.append(probe.getsockname()[0])
    except OSError:
        pass
    for address in candidates:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind((address, 0))
        except OSError:
            sock.close()
            continue
        return sock
    return None


def test_port_in_use_raises_a_clear_error(firmware):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as blocker:
        blocker.bind((LOCALHOST, 0))
        port = blocker.getsockname()[1]
        dev = make_device(firmware, port)
        with pytest.raises(DevicePortInUseError) as caught:
            dev.open()
        assert caught.value.key == "device_port_in_use"
        assert caught.value.fmt == {"port": port}
        assert not dev.is_open


def test_unresolvable_host_is_an_open_error(local_port):
    dev = UdpGyroDevice("host.invalid", 1, local_port, bind_host=LOCALHOST)
    with pytest.raises(DeviceError) as caught:
        dev.open()
    assert caught.value.key == "device_open_failed"
    assert not dev.is_open


def test_keepalive_registers_again(firmware, device):
    assert firmware.wait_for_registrations(1)
    before = firmware.registrations
    device.keepalive()
    device.keepalive()
    assert firmware.wait_for_registrations(before + 2)


class _BrokenSocket:
    def sendto(self, *_args):
        raise OSError("network down")

    def close(self):
        pass


def test_keepalive_swallows_send_errors(device, monkeypatch):
    real = device._sock  # noqa: SLF001
    monkeypatch.setattr(device, "_sock", _BrokenSocket())
    device.keepalive()  # must not raise
    monkeypatch.setattr(device, "_sock", real)


def test_close_is_idempotent_and_read_after_close_is_empty(firmware, local_port):
    dev = make_device(firmware, local_port)
    dev.close()  # before open
    dev.open()
    dev.close()
    dev.close()
    assert not dev.is_open
    assert dev.read(0.05) == []
    dev.keepalive()  # no-op
    dev.open()  # re-open works and frees the port again on close
    assert dev.is_open
    dev.close()


def test_registration_failure_does_not_fail_open(local_port):
    dev = UdpGyroDevice(LOCALHOST, 0, local_port, http_port=free_udp_port(), bind_host=LOCALHOST)
    dev.open()  # sending to port 0 fails; the keep-alive retries later
    try:
        assert dev.is_open
        dev.keepalive()
    finally:
        dev.close()


def test_read_times_out_without_data(local_port):
    with FakeFirmware(data_port=local_port, http=False) as fake:
        fake.stop_sending()
        dev = make_device(fake, local_port)
        dev.open()
        try:
            start = time.monotonic()
            assert dev.read(0.1) == []
            assert 0.08 <= time.monotonic() - start < 1.0
            assert dev.stats().data_age_s is None
        finally:
            dev.close()
