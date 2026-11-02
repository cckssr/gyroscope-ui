"""Device factory: the real UDP device or the simulation, built from ``config.json``."""

from __future__ import annotations

import dataclasses
from typing import Any

from gyroscope_ui.core.protocol import Limits
from gyroscope_ui.core.simulation import SimulationParams
from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.infrastructure.devices.base import GyroDevice
from gyroscope_ui.infrastructure.devices.udp_device import UdpGyroDevice
from gyroscope_ui.infrastructure.mocks.mock_gyroscope import MockGyroscope


def _coerce(value: Any, default: Any) -> Any:
    """``value`` as the type of the dataclass default (JSON has no float/int distinction)."""
    if isinstance(default, bool):
        return bool(value)
    if isinstance(default, int):
        return int(value)
    return None if value is None else float(value)


def _from_section(cls: type, section: dict[str, Any]) -> Any:
    """Instance of the dataclass ``cls`` with the fields that are present in ``section``."""
    kwargs = {
        f.name: _coerce(section[f.name], getattr(cls(), f.name))
        for f in dataclasses.fields(cls)
        if f.name in section
    }
    return cls(**kwargs)


def create_device(config: AppConfig, simulate: bool) -> GyroDevice:
    """A closed device: ``MockGyroscope`` (``simulation.*``) or ``UdpGyroDevice`` (``device.*``)."""
    if simulate:
        sim = config.section("simulation")
        return MockGyroscope(
            _from_section(SimulationParams, sim),
            time_scale=float(sim.get("time_scale", 1.0)),
            max_batch=int(sim.get("max_batch", 500)),
        )
    get = config.get
    return UdpGyroDevice(
        str(get("device.host", "192.168.4.1")),
        int(get("device.port", 12345)),
        int(get("device.local_port", 12345)),
        http_port=int(get("device.http_port", 80)),
        info_timeout_s=float(get("device.info_timeout_s", 1.0)),
        limits=_from_section(Limits, config.get("device.limits", {}) or {}),
        pulses_per_revolution=int(get("device.pulses_per_revolution", 1)),
    )
