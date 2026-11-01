"""Device factory: simulated or real device built from config.json (nothing is opened)."""

from __future__ import annotations

from gyroscope_ui.core.protocol import Limits
from gyroscope_ui.infrastructure.config import AppConfig, load_config
from gyroscope_ui.infrastructure.devices.base import GyroDevice
from gyroscope_ui.infrastructure.devices.discovery import create_device
from gyroscope_ui.infrastructure.devices.udp_device import UdpGyroDevice
from gyroscope_ui.infrastructure.mocks.mock_gyroscope import MockGyroscope


def test_simulate_builds_a_mock_from_the_simulation_section():
    config = load_config(
        overrides={
            "simulation": {
                "time_scale": 0.25,
                "max_batch": 77,
                "rate_hz": 50,
                "start_frequency_hz": 9.5,
                "firmware_quirk": True,
                "seed": 4,
                "protocol_version": 2,
                "restart_at_s": 12,
                "drop_probability": 0.1,
            }
        }
    )
    device = create_device(config, simulate=True)
    assert isinstance(device, MockGyroscope) and isinstance(device, GyroDevice)
    assert not device.is_open
    assert device.time_scale == 0.25 and device.max_batch == 77
    p = device.params
    assert (p.rate_hz, p.start_frequency_hz, p.firmware_quirk, p.seed) == (50.0, 9.5, True, 4)
    assert (p.protocol_version, p.restart_at_s, p.drop_probability) == (2, 12.0, 0.1)
    assert isinstance(p.rate_hz, float) and isinstance(p.seed, int)
    assert p.spin_down_tau_s == 120.0  # from the shipped config


def test_shipped_config_gives_a_working_mock():
    device = create_device(load_config(), simulate=True)
    assert device.time_scale == 1.0 and device.max_batch == 500
    assert device.params.rate_hz == 100.0


def test_empty_config_falls_back_to_the_defaults():
    device = create_device(AppConfig({}), simulate=True)
    assert device.time_scale == 1.0 and device.params.start_frequency_hz == 15.0
    real = create_device(AppConfig({}), simulate=False)
    assert (real.host, real.port, real.local_port, real.http_port) == (
        "192.168.4.1",
        12345,
        12345,
        80,
    )


def test_real_builds_an_unopened_udp_device_from_the_device_section():
    config = load_config(
        overrides={
            "device": {
                "host": "10.0.0.7",
                "port": 4000,
                "local_port": 4001,
                "http_port": 8080,
                "info_timeout_s": 0.25,
                "pulses_per_revolution": 2,
                "limits": {"frequency_hz_max": 500, "gyro_rad_s_max": 20},
            }
        }
    )
    device = create_device(config, simulate=False)
    assert isinstance(device, UdpGyroDevice) and isinstance(device, GyroDevice)
    assert not device.is_open
    assert (device.host, device.port, device.local_port, device.http_port) == (
        "10.0.0.7",
        4000,
        4001,
        8080,
    )
    assert device._info_timeout_s == 0.25  # noqa: SLF001
    assert device._pulses == 2  # noqa: SLF001
    assert device._limits == Limits(500.0, 200.0, 20.0)  # noqa: SLF001
    assert device.info.address == "10.0.0.7:4000"


def test_shipped_config_gives_the_documented_real_device():
    device = create_device(load_config(), simulate=False)
    assert (device.host, device.port, device.local_port, device.http_port) == (
        "192.168.4.1",
        12345,
        12345,
        80,
    )
    assert device._limits == Limits()  # noqa: SLF001
