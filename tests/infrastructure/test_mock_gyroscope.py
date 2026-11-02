"""MockGyroscope: pacing, catch-up, loss, restart and the command interface."""

from __future__ import annotations

import threading

import pytest

from gyroscope_ui.core.models import LinkStats
from gyroscope_ui.core.simulation import GyroSimulation, SimulationParams
from gyroscope_ui.infrastructure.devices.base import DeviceError, GyroDevice, LinkMeter
from gyroscope_ui.infrastructure.mocks.mock_gyroscope import MockGyroscope


class FakeClock:
    """Manual clock; ``sleep`` advances it."""

    def __init__(self) -> None:
        self.now = 100.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def make(params: SimulationParams | None = None, **kwargs) -> tuple[MockGyroscope, FakeClock]:
    clock = FakeClock()
    device = MockGyroscope(params, clock=clock, sleep=clock.sleep, **kwargs)
    return device, clock


def test_is_a_gyro_device_with_simulation_info():
    device, _ = make(SimulationParams(protocol_version=2))
    assert isinstance(device, GyroDevice)
    assert not device.is_open
    assert device.info.device_id == "SIM0001"
    assert device.info.simulated and device.info.protocol_version == 2
    assert device.info.address == "simulation" and device.info.firmware_version == "sim"
    device.open()
    assert device.is_open
    device.keepalive()
    device.close()
    device.close()
    assert not device.is_open and device.read(0.1) == []


def test_samples_are_paced_by_simulated_time():
    device, clock = make(SimulationParams(rate_hz=100.0), time_scale=0.1)
    device.open()
    first = device.read(0.5)  # sample 0 is due at once
    assert [s.device_ms for s in first] == [0]
    clock.now += 0.1  # 0.1 s real = 1 s simulated = 100 samples
    samples = device.read(0.5)
    assert [s.device_ms for s in samples] == [10 * k for k in range(1, 101)]
    assert samples[-1].host_time_s == pytest.approx(clock.now)
    assert all(a.host_time_s < b.host_time_s for a, b in zip(samples, samples[1:], strict=False))


def test_sleeps_one_sample_period_when_nothing_is_due():
    device, clock = make(SimulationParams(rate_hz=100.0), time_scale=0.5)
    device.open()
    device.read(0.5)
    samples = device.read(10.0)
    assert clock.sleeps == [pytest.approx(0.5 / 100.0)]  # time_scale / rate_hz, not the timeout
    assert len(samples) == 1
    clock.sleeps.clear()
    device.read(0.001)
    assert clock.sleeps == [0.001]  # never longer than the timeout


def test_max_batch_catches_up_over_several_reads():
    device, clock = make(SimulationParams(rate_hz=100.0), max_batch=30)
    device.open()
    clock.now += 1.0  # 101 samples due (index 0..100)
    first = device.read(0.1)
    assert [s.device_ms for s in first] == [10 * k for k in range(30)]
    counts = [len(device.read(0.1)) for _ in range(3)]
    assert counts == [30, 30, 11]
    clock.now += 0.02
    assert [s.device_ms for s in device.read(0.1)] == [1010, 1020]  # caught up: only new samples


def test_matches_the_simulation_and_has_no_seq_in_v1():
    params = SimulationParams(seed=7)
    device, clock = make(params)
    device.open()
    clock.now += 0.5
    samples = device.read(0.1)
    sim = GyroSimulation(params)
    assert len(samples) == 51
    for k, sample in enumerate(samples):
        expected = sim.sample_at(k / params.rate_hz)
        assert sample.seq is None
        assert sample.frequency_hz == expected.frequency_hz
        assert sample.gyro_z_rad_s == expected.gyro_z_rad_s


def test_protocol_v2_numbers_the_samples_and_drops_leave_gaps():
    params = SimulationParams(protocol_version=2, drop_probability=0.3, seed=3)
    device, clock = make(params)
    device.open()
    clock.now += 2.0
    samples = device.read(0.1)
    seqs = [s.seq for s in samples]
    assert None not in seqs
    sim = GyroSimulation(params)
    dropped = {k for k in range(201) if sim.should_drop(k)}
    assert dropped and len(samples) == 201 - len(dropped)
    assert seqs == [k for k in range(201) if k not in dropped]
    assert device.stats().received == len(samples)
    assert device.stats().protocol_version == 2


def test_restart_resets_the_device_clock():
    device, clock = make(SimulationParams(restart_at_s=1.0, rate_hz=100.0))
    device.open()
    clock.now += 2.0
    ms = [s.device_ms for s in device.read(0.1)]
    assert ms[:3] == [0, 10, 20]
    i = ms.index(0, 1)  # the second 0: reset at t = 1 s
    assert i == 100 and ms[i - 1] == 990 and ms[-1] == 1000


def test_pause_stream_stops_samples_without_catching_up():
    device, clock = make(SimulationParams(rate_hz=100.0, protocol_version=2))
    device.open()
    clock.now += 0.1
    assert len(device.read(0.1)) == 11
    device.pause_stream(True)
    clock.now += 5.0
    assert device.read(0.05) == [] and device.read(0.05) == []
    device.pause_stream(False)
    clock.now += 0.1
    resumed = device.read(0.1)
    assert 9 <= len(resumed) <= 12  # about 0.1 s worth, not 5 s
    assert resumed[0].device_ms > 5000
    assert resumed[0].seq == 11  # the silent period leaves no gap in the sequence


def test_fail_next_read_raises_once():
    device, _ = make()
    device.open()
    device.fail_next_read()
    with pytest.raises(DeviceError) as caught:
        device.read(0.1)
    assert caught.value.key == "device_io_failed"
    assert device.read(0.1)  # works again
    device.fail_next_read("device_timeout")
    with pytest.raises(DeviceError) as caught:
        device.read(0.1)
    assert caught.value.key == "device_timeout"


def test_kick_restarts_the_spin():
    quiet = SimulationParams(
        noise_frequency_hz=0.0, start_frequency_hz=10.0, spin_down_tau_s=10.0, rate_hz=10.0
    )
    device, clock = make(quiet)
    device.open()
    clock.now += 10.0
    assert device.read(0.1)[-1].frequency_hz == pytest.approx(10.0 * 0.3679, rel=1e-3)
    device.kick(20.0)
    clock.now += 0.1
    assert device.read(0.1)[-1].frequency_hz == pytest.approx(20.0, rel=0.02)
    device.kick()
    clock.now += 0.1
    assert device.read(0.1)[-1].frequency_hz == pytest.approx(10.0, rel=0.02)


def test_commands_are_thread_safe():
    device = MockGyroscope(SimulationParams(), time_scale=0.01)
    device.open()
    stop = threading.Event()

    def hammer():
        while not stop.is_set():
            device.kick(12.0)
            device.pause_stream(False)

    thread = threading.Thread(target=hammer)
    thread.start()
    try:
        total = sum(len(device.read(0.01)) for _ in range(30))
    finally:
        stop.set()
        thread.join()
    assert total > 0


def test_reopen_starts_again():
    device, clock = make()
    device.open()
    clock.now += 1.0
    assert len(device.read(0.1)) > 50
    device.close()
    device.open()
    assert [s.device_ms for s in device.read(0.1)] == [0]
    assert device.stats().received == 1


def test_stats_use_a_sliding_window_of_valid_samples():
    device, clock = make(SimulationParams(rate_hz=100.0), time_scale=1.0)
    device.open()
    assert device.stats() == LinkStats(0.0, 0, 0, None, 1)
    for _ in range(40):
        clock.now += 0.05
        device.read(0.05)
    stats = device.stats()
    assert stats.rate_hz == pytest.approx(100.0, rel=0.05)
    assert stats.received == 201 and stats.data_age_s == 0.0
    clock.now += 3.0  # data stop: window empties
    stats = device.stats()
    assert stats.rate_hz == 0.0 and stats.data_age_s == pytest.approx(3.0)


def test_link_meter_counts_invalid_and_ramps_up():
    clock = FakeClock()
    meter = LinkMeter(clock, window_s=2.0)
    clock.now += 1.0
    meter.add(100, 2)
    stats = meter.snapshot(1)
    assert (stats.received, stats.invalid, stats.protocol_version) == (100, 2, 1)
    assert stats.rate_hz == pytest.approx(100.0)  # elapsed 1 s < window: divided by elapsed
    meter.reset()
    assert meter.snapshot().received == 0


def test_rejects_a_bad_time_scale():
    with pytest.raises(ValueError):
        MockGyroscope(time_scale=0.0)
