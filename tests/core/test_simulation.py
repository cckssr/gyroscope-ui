from __future__ import annotations

import math
import re

import pytest

from gyroscope_ui.core.protocol import parse_line
from gyroscope_ui.core.simulation import GyroSimulation, SimulationParams

LINE_V1 = re.compile(r"^\d+,(-?\d+\.\d{4},){6}-?\d+\.\d{4}\r\n$")
LINE_V2 = re.compile(r"^\d+,(-?\d+\.\d{4},){6}-?\d+\.\d{4},\d+\r\n$")
QUIET = SimulationParams(
    noise_frequency_hz=0.0, noise_accel_m_s2=0.0, noise_gyro_rad_s=0.0, nutation_rad_s=0.0
)


def test_same_seed_gives_identical_output_and_other_seeds_differ():
    a, b = GyroSimulation(SimulationParams(seed=5)), GyroSimulation(SimulationParams(seed=5))
    times = [i * 0.01 for i in range(200)]
    assert [a.line_at(t) for t in times] == [b.line_at(t) for t in times]
    c = GyroSimulation(SimulationParams(seed=6))
    assert [a.line_at(t) for t in times] != [c.line_at(t) for t in times]


def test_sample_at_is_independent_of_the_call_order():
    sim = GyroSimulation()
    first = sim.sample_at(3.0)
    sim.sample_at(1.0)
    assert sim.sample_at(3.0) == first


def test_line_format_v1_and_v2():
    sim = GyroSimulation()
    assert LINE_V1.match(sim.line_at(1.234))
    sim2 = GyroSimulation(SimulationParams(protocol_version=2))
    line = sim2.line_at(1.234, seq=77)
    assert LINE_V2.match(line) and line.rstrip().endswith(",77")
    with pytest.raises(ValueError):
        sim2.line_at(1.0)


def test_line_roundtrip_through_the_parser():
    sim = GyroSimulation(SimulationParams(protocol_version=2))
    for t in (0.0, 0.01, 1.5, 33.33, 119.99, 500.0):
        sample = sim.sample_at(t, seq=5)
        parsed = parse_line(sim.line_at(t, seq=5))
        assert parsed.device_ms == sample.device_ms == round(t * 1000)
        assert parsed.seq == 5
        for name in (
            "frequency_hz",
            "accel_x_m_s2",
            "accel_y_m_s2",
            "accel_z_m_s2",
            "gyro_x_rad_s",
            "gyro_y_rad_s",
            "gyro_z_rad_s",
        ):
            assert getattr(parsed, name) == pytest.approx(getattr(sample, name), abs=6e-5)


def test_d7_simulated_clock_value_with_repeated_digits_parses():
    sim = GyroSimulation()
    line = sim.line_at(2000.0)
    assert line.startswith("2000000,")
    assert parse_line(line).device_ms == 2000000


def test_exponential_spin_down_and_kick():
    sim = GyroSimulation(SimulationParams(start_frequency_hz=15.0, spin_down_tau_s=120.0))
    assert sim.frequency_at(0.0) == 15.0
    assert sim.frequency_at(120.0) == pytest.approx(15.0 / math.e)
    sim.kick(200.0)
    assert sim.frequency_at(200.0) == 15.0
    assert sim.frequency_at(320.0) == pytest.approx(15.0 / math.e)
    sim.kick(400.0, frequency_hz=8.0)
    assert sim.frequency_at(400.0) == 8.0


def test_precession_increases_as_the_frequency_decreases():
    sim = GyroSimulation(QUIET)
    omegas = [sim.precession_rad_s(f) for f in (15.0, 10.0, 8.0, 7.0)]
    assert omegas == sorted(omegas) and len(set(omegas)) == 4
    # omega_p = m g l / (I 2 pi f) with I = m r^2 / 2
    expected = 1.5 * 9.81 * 0.1 / (0.5 * 1.5 * 0.1**2 * 2 * math.pi * 10.0)
    assert sim.precession_rad_s(10.0) == pytest.approx(expected)
    assert sim.precession_rad_s(0.0) == 5.0  # clipped
    assert sim.precession_rad_s(0.001) == 5.0


def test_measured_gyro_z_follows_the_precession_law():
    sim = GyroSimulation(QUIET)
    early, late = sim.sample_at(1.0), sim.sample_at(240.0)
    assert late.gyro_z_rad_s > early.gyro_z_rad_s
    assert early.gyro_z_rad_s == pytest.approx(sim.precession_rad_s(sim.frequency_at(1.0)))
    assert early.accel_z_m_s2 == pytest.approx(9.81)


def test_sample_values_are_plausible_and_pass_the_parser_limits():
    sim = GyroSimulation()
    for i in range(0, 60000, 7):
        sample = sim.sample_at(i * 0.01)
        assert 0.0 <= sample.frequency_hz < 20.0
        assert abs(sample.accel_z_m_s2 - 9.81) < 1.0
        assert abs(sample.gyro_z_rad_s) < 10.0
        parse_line(sim.line_at(i * 0.01))


def test_nutation_is_damped():
    sim = GyroSimulation(SimulationParams(noise_gyro_rad_s=0.0, noise_frequency_hz=0.0))

    def spread(t0: float) -> float:
        values = [sim.sample_at(t0 + i * 0.01).gyro_z_rad_s for i in range(100)]
        return max(values) - min(values)

    assert spread(0.0) > spread(30.0)


def test_device_clock_restarts_at_restart_at_s():
    sim = GyroSimulation(SimulationParams(restart_at_s=10.0))
    assert sim.sample_at(9.99).device_ms == 9990
    assert sim.sample_at(10.0).device_ms == 0
    assert sim.sample_at(10.5).device_ms == 500


def test_should_drop_is_seeded_and_matches_the_probability():
    sim = GyroSimulation(SimulationParams(drop_probability=0.1, seed=3))
    drops = [sim.should_drop(i) for i in range(5000)]
    again = [
        GyroSimulation(SimulationParams(drop_probability=0.1, seed=3)).should_drop(i)
        for i in range(50)
    ]
    assert drops[:50] == again
    assert 0.07 < sum(drops) / len(drops) < 0.13
    assert not any(GyroSimulation().should_drop(i) for i in range(100))


def test_firmware_quirk_reports_zero_when_the_value_stays_constant():
    params = SimulationParams(
        firmware_quirk=True,
        spin_down_tau_s=1e9,  # steady rotation
        noise_frequency_hz=0.0,
    )
    sim = GyroSimulation(params)
    values = [(i * 0.1, sim.sample_at(i * 0.1).frequency_hz) for i in range(60)]
    assert all(f == pytest.approx(15.0) for t, f in values if t < 2.0)
    assert all(f == 0.0 for t, f in values if t >= 2.0)
    sim.kick(10.0)  # a new spin changes the value: it is reported again
    assert sim.sample_at(10.0).frequency_hz == pytest.approx(15.0)


def test_without_the_quirk_a_steady_rotation_keeps_its_value():
    sim = GyroSimulation(SimulationParams(spin_down_tau_s=1e9, noise_frequency_hz=0.0))
    assert sim.sample_at(30.0).frequency_hz == pytest.approx(15.0)


def test_quirk_does_not_trigger_during_a_normal_spin_down():
    sim = GyroSimulation(SimulationParams(firmware_quirk=True))
    freqs = [sim.sample_at(i * 0.01).frequency_hz for i in range(3000)]  # 30 s, f > 11 Hz
    assert min(freqs) > 10.0
