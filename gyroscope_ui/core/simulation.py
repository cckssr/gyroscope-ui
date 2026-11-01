"""Physics of the simulated Kreisel (used by the mock device and the tests; CONCEPT 7).

The disc spins down exponentially, ``f(t) = f0 exp(-(t - t_kick)/tau)``, and precesses about the
vertical axis with ``omega_p = m g l / (I 2 pi f)``, ``I = m r^2 / 2`` (clipped at
``precession_max_rad_s`` for a standing disc). A damped nutation rides on ``gyro`` and the
sensors carry seeded Gaussian noise. ``sample_at`` is a pure function of the time, the seed and
the last ``kick`` (except for the optional firmware quirk, which needs calls in time order).

Pure NumPy, no Qt, no I/O, no clock: callers pass the simulated time.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from gyroscope_ui.core.models import Sample

GRAVITY_M_S2 = 9.81
QUIRK_HOLD_S = 2.0  # firmware v1: value constant for this long ...
QUIRK_DELTA_HZ = 0.05  # ... within this band is reported as 0 Hz
_NUTATION_RATIO = 2.0  # nutation frequency / spin frequency of a thin disc (I_z / I_x)


@dataclass(frozen=True)
class SimulationParams:
    start_frequency_hz: float = 15.0
    spin_down_tau_s: float = 120.0
    rate_hz: float = 100.0
    mass_kg: float = 1.5
    radius_m: float = 0.1
    lever_m: float = 0.1
    nutation_rad_s: float = 0.3
    nutation_tau_s: float = 5.0
    noise_frequency_hz: float = 0.02
    noise_accel_m_s2: float = 0.05
    noise_gyro_rad_s: float = 0.01
    precession_max_rad_s: float = 5.0
    firmware_quirk: bool = False
    drop_probability: float = 0.0
    restart_at_s: float | None = None
    protocol_version: int = 1
    seed: int = 1


class GyroSimulation:
    """Deterministic generator of samples and firmware lines for one simulated device."""

    def __init__(self, params: SimulationParams | None = None) -> None:
        self.params = params if params is not None else SimulationParams()
        self._kick_t_s = 0.0
        self._kick_frequency_hz = self.params.start_frequency_hz
        self._quirk_ref_hz = math.nan
        self._quirk_ref_t_s = 0.0

    # --- physics -----------------------------------------------------------------------------

    def kick(self, t_s: float, frequency_hz: float | None = None) -> None:
        """Restart the spin at time ``t_s`` (default: the configured start frequency)."""
        self._kick_t_s = t_s
        self._kick_frequency_hz = (
            self.params.start_frequency_hz if frequency_hz is None else frequency_hz
        )
        self._quirk_ref_hz = math.nan

    def frequency_at(self, t_s: float) -> float:
        """Noise-free rotation frequency; before the last kick the kick frequency."""
        dt = max(0.0, t_s - self._kick_t_s)
        return self._kick_frequency_hz * math.exp(-dt / self.params.spin_down_tau_s)

    def precession_rad_s(self, frequency_hz: float) -> float:
        """Precession rate about z for a spin frequency, clipped at ``precession_max_rad_s``."""
        p = self.params
        maximum = p.precession_max_rad_s
        if frequency_hz <= 0.0:
            return maximum
        inertia = 0.5 * p.mass_kg * p.radius_m**2
        omega = p.mass_kg * GRAVITY_M_S2 * p.lever_m / (inertia * 2.0 * math.pi * frequency_hz)
        return min(omega, maximum)

    def _nutation(self, t_s: float) -> tuple[float, float]:
        """Amplitude and phase of the damped nutation."""
        p = self.params
        dt = max(0.0, t_s - self._kick_t_s)
        amplitude = p.nutation_rad_s * math.exp(-dt / p.nutation_tau_s)
        spin_turns = (
            self._kick_frequency_hz * p.spin_down_tau_s * (1.0 - math.exp(-dt / p.spin_down_tau_s))
        )
        return amplitude, 2.0 * math.pi * _NUTATION_RATIO * spin_turns

    def _noise(self, t_s: float) -> np.ndarray:
        rng = np.random.default_rng([self.params.seed, 0, int(round(t_s * 1000))])
        return rng.standard_normal(7)

    def _quirk(self, t_s: float, frequency_hz: float) -> float:
        """Firmware v1: report 0 Hz once the value stayed within 0.05 Hz for 2 s."""
        restart_reference = (
            math.isnan(self._quirk_ref_hz)
            or t_s < self._quirk_ref_t_s
            or abs(frequency_hz - self._quirk_ref_hz) >= QUIRK_DELTA_HZ
        )
        if restart_reference:
            self._quirk_ref_hz, self._quirk_ref_t_s = frequency_hz, t_s
        elif t_s - self._quirk_ref_t_s >= QUIRK_HOLD_S:
            return 0.0
        return frequency_hz

    # --- output ------------------------------------------------------------------------------

    def device_ms(self, t_s: float) -> int:
        """Device clock for simulated time ``t_s`` (restarts from 0 at ``restart_at_s``)."""
        restart = self.params.restart_at_s
        if restart is not None and t_s >= restart:
            t_s -= restart
        return int(round(t_s * 1000.0))

    def sample_at(self, t_s: float, seq: int | None = None) -> Sample:
        p = self.params
        noise = self._noise(t_s)
        f_true = self.frequency_at(t_s)
        frequency = max(0.0, f_true + p.noise_frequency_hz * float(noise[0]))
        if p.firmware_quirk:
            frequency = self._quirk(t_s, frequency)
        amplitude, phase = self._nutation(t_s)
        na, ng = p.noise_accel_m_s2, p.noise_gyro_rad_s
        gyro_z = self.precession_rad_s(f_true) + amplitude * math.sin(phase) + ng * float(noise[6])
        return Sample(
            device_ms=self.device_ms(t_s),
            frequency_hz=frequency,
            accel_x_m_s2=na * float(noise[1]) + 0.1 * amplitude * math.cos(phase),
            accel_y_m_s2=na * float(noise[2]) + 0.1 * amplitude * math.sin(phase),
            accel_z_m_s2=GRAVITY_M_S2 + na * float(noise[3]),
            gyro_x_rad_s=0.5 * amplitude * math.cos(phase) + ng * float(noise[4]),
            gyro_y_rad_s=0.5 * amplitude * math.sin(phase) + ng * float(noise[5]),
            gyro_z_rad_s=gyro_z,
            seq=seq,
        )

    def line_at(self, t_s: float, seq: int | None = None) -> str:
        """The firmware's data line for ``t_s`` (PROTOCOL 3.2; 9 fields for protocol v2)."""
        v2 = self.params.protocol_version == 2
        if v2 and seq is None:
            raise ValueError("seq is required for protocol version 2")
        s = self.sample_at(t_s, seq)
        line = (
            f"{s.device_ms},{s.frequency_hz:.4f},{s.accel_x_m_s2:.4f},{s.accel_y_m_s2:.4f},"
            f"{s.accel_z_m_s2:.4f},{s.gyro_x_rad_s:.4f},{s.gyro_y_rad_s:.4f},{s.gyro_z_rad_s:.4f}"
        )
        return f"{line},{seq}\r\n" if v2 else f"{line}\r\n"

    def should_drop(self, index: int) -> bool:
        """Whether datagram number ``index`` is lost (seeded, independent of other calls)."""
        probability = self.params.drop_probability
        if probability <= 0.0:
            return False
        rng = np.random.default_rng([self.params.seed, 1, index])
        return bool(rng.random() < probability)
