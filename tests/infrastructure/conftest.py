"""Fixtures of the infrastructure tests: offscreen Qt, loopback fake firmware, free UDP ports."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from fake_firmware import FakeFirmware, free_udp_port  # noqa: E402

from gyroscope_ui.core.simulation import SimulationParams  # noqa: E402
from gyroscope_ui.infrastructure.mocks.mock_gyroscope import MockGyroscope  # noqa: E402


@pytest.fixture
def local_port() -> int:
    """A free local UDP port for the host side (never the real port 12345)."""
    return free_udp_port()


@pytest.fixture
def firmware(local_port):
    """Fake firmware v1 sending its data to ``local_port``."""
    with FakeFirmware(data_port=local_port) as fake:
        yield fake


@pytest.fixture
def mock_device():
    """Opened mock running 100x faster than real time."""
    device = MockGyroscope(SimulationParams(), time_scale=0.01)
    device.open()
    yield device
    device.close()
