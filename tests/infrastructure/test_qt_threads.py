"""ConnectWorker and AcquisitionWorker (pytest-qt, mock device, loopback fake firmware)."""

from __future__ import annotations

import threading
import time
from concurrent.futures import CancelledError

import pytest
from fake_firmware import LOCALHOST, FakeFirmware
from PySide6.QtCore import qInstallMessageHandler

from gyroscope_ui.core.models import LinkState, LinkStats, SampleBatch
from gyroscope_ui.core.simulation import SimulationParams
from gyroscope_ui.infrastructure.devices.base import DeviceError, DevicePortInUseError
from gyroscope_ui.infrastructure.devices.udp_device import UdpGyroDevice
from gyroscope_ui.infrastructure.mocks.mock_gyroscope import MockGyroscope
from gyroscope_ui.infrastructure.qt_threads import AcquisitionWorker, ConnectWorker

WAIT_MS = 10_000
FAST = {
    "batch_interval_s": 0.02,
    "stats_interval_s": 0.1,
    "keepalive_s": 0.1,
    "data_timeout_s": 0.3,
    "lost_after_s": 0.8,
    "read_timeout_s": 0.02,
}


@pytest.fixture
def qt_messages():
    """Collects Qt log messages (the 'QThread: Destroyed while thread is still running' line)."""
    seen: list[str] = []
    previous = qInstallMessageHandler(lambda _mode, _ctx, text: seen.append(text))
    yield seen
    qInstallMessageHandler(previous)


def assert_no_thread_complaints(messages: list[str]) -> None:
    assert not [m for m in messages if "Destroyed while thread" in m], messages


@pytest.fixture
def started():
    """Start workers and make sure they are stopped and joined, whatever the test does."""
    workers: list[AcquisitionWorker] = []

    def start(worker: AcquisitionWorker) -> AcquisitionWorker:
        workers.append(worker)
        worker.start()
        return worker

    yield start
    for worker in workers:
        worker.abort()
        assert worker.wait(5000)


def make_worker(device, **overrides) -> AcquisitionWorker:
    return AcquisitionWorker(device, **{**FAST, **overrides})


def mock(**params) -> MockGyroscope:
    # 100 Hz of simulated time at time_scale 0.1 = 1000 samples per second of real time
    device = MockGyroscope(SimulationParams(**params), time_scale=0.1)
    device.open()
    return device


class Recorder:
    """Collects the signals of a worker (appended on the GUI thread)."""

    def __init__(self, worker: AcquisitionWorker) -> None:
        self.batches: list[SampleBatch] = []
        self.states: list[str] = []
        self.stats: list[LinkStats] = []
        self.command_failed: list[str] = []
        self.failed: list[str] = []
        worker.samples_ready.connect(self.batches.append)
        worker.link_changed.connect(self.states.append)
        worker.stats_ready.connect(self.stats.append)
        worker.command_failed.connect(self.command_failed.append)
        worker.failed.connect(self.failed.append)

    @property
    def sample_count(self) -> int:
        return sum(len(b) for b in self.batches)


# ---- ConnectWorker ---------------------------------------------------------------------------


def test_connect_worker_opens_the_device(qtbot):
    device = MockGyroscope()
    worker = ConnectWorker(device)
    with qtbot.waitSignal(worker.connected, timeout=WAIT_MS) as blocker:
        worker.start()
    assert blocker.args == [device] and device.is_open
    assert worker.wait(5000)
    device.close()


class FailingDevice:
    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    def open(self) -> None:
        raise self.exc


@pytest.mark.parametrize(
    ("exc", "key"),
    [
        (DevicePortInUseError(port=12345), "device_port_in_use"),
        (DeviceError("device_timeout"), "device_timeout"),
        (RuntimeError("boom"), "device_open_failed"),
    ],
)
def test_connect_worker_reports_the_message_key(qtbot, exc, key):
    worker = ConnectWorker(FailingDevice(exc))
    errors: list = []
    worker.failed_error.connect(errors.append)
    with qtbot.waitSignal(worker.failed, timeout=WAIT_MS) as blocker:
        worker.start()
    assert blocker.args == [key]
    qtbot.waitUntil(lambda: bool(errors), timeout=WAIT_MS)
    assert errors == [exc]
    assert worker.wait(5000)


def test_connect_worker_port_in_use_keeps_the_format_arguments(qtbot):
    worker = ConnectWorker(FailingDevice(DevicePortInUseError(port=4711)))
    errors: list = []
    worker.failed_error.connect(errors.append)
    worker.start()
    qtbot.waitUntil(lambda: bool(errors), timeout=WAIT_MS)
    assert errors[0].fmt == {"port": 4711}
    assert worker.wait(5000)


# ---- AcquisitionWorker with the mock ---------------------------------------------------------


def test_batches_arrive_and_the_link_becomes_connected(qtbot, started):
    worker = make_worker(mock())
    rec = Recorder(worker)
    started(worker)
    qtbot.waitUntil(lambda: rec.sample_count >= 200, timeout=WAIT_MS)
    assert all(isinstance(b, SampleBatch) and len(b) > 0 for b in rec.batches)
    assert rec.states == ["connecting", "connected"]
    ms = [m for b in rec.batches for m in b.device_ms.tolist()]
    assert ms == sorted(ms) and len(set(ms)) == len(ms)  # nothing lost, nothing duplicated
    qtbot.waitUntil(lambda: bool(rec.stats), timeout=WAIT_MS)
    assert isinstance(rec.stats[0], LinkStats) and rec.stats[0].received > 0


def test_batches_respect_the_batch_interval(qtbot, started):
    worker = make_worker(mock(), batch_interval_s=0.1)
    rec = Recorder(worker)
    started(worker)
    qtbot.waitUntil(lambda: len(rec.batches) >= 5, timeout=WAIT_MS)
    # host_time_s is the time the mock produced the sample, independent of GUI event timing
    ends = [float(b.host_time_s[-1]) for b in rec.batches]
    gaps = [b - a for a, b in zip(ends, ends[1:], strict=False)]
    assert min(gaps) > 0.08  # about 10 batches/s, not one per read


def test_pause_gives_stale_then_lost_and_resume_connects_again(qtbot, started):
    device = mock()
    worker = make_worker(device)
    rec = Recorder(worker)
    started(worker)
    qtbot.waitUntil(lambda: "connected" in rec.states, timeout=WAIT_MS)
    device.pause_stream(True)
    qtbot.waitUntil(lambda: "lost" in rec.states, timeout=WAIT_MS)
    assert rec.states == ["connecting", "connected", "stale", "lost"]
    device.pause_stream(False)
    qtbot.waitUntil(lambda: rec.states[-1] == "connected", timeout=WAIT_MS)
    assert rec.states == ["connecting", "connected", "stale", "lost", "connected"]
    assert [LinkState(s) for s in rec.states]  # all values are valid LinkState values


def test_no_data_at_all_goes_stale_then_lost_from_the_start(qtbot, started):
    device = mock()
    device.pause_stream(True)
    worker = make_worker(device)
    rec = Recorder(worker)
    started(worker)
    qtbot.waitUntil(lambda: "lost" in rec.states, timeout=WAIT_MS)
    assert rec.states == ["connecting", "stale", "lost"]
    assert rec.batches == []


def test_keepalive_is_sent_in_every_state(qtbot, started):
    class Counting(MockGyroscope):
        keepalives = 0

        def keepalive(self) -> None:
            Counting.keepalives += 1

    device = Counting(SimulationParams(), time_scale=0.1)
    device.open()
    device.pause_stream(True)
    started(make_worker(device))
    qtbot.waitUntil(lambda: Counting.keepalives >= 4, timeout=WAIT_MS)


def test_run_in_thread_returns_the_result_on_the_worker_thread(qtbot, started):
    worker = make_worker(mock())
    started(worker)
    threads: list[str] = []

    def command(device):
        threads.append(threading.current_thread().name)
        return device.info.device_id

    future = worker.run_in_thread(command)
    assert future.result(timeout=10) == "SIM0001"
    assert threads and threads[0] != threading.current_thread().name


def test_failing_command_emits_command_failed_and_the_future_raises(qtbot, started):
    worker = make_worker(mock())
    rec = Recorder(worker)
    started(worker)

    def broken(_device):
        raise DeviceError("device_timeout")

    def crashing(_device):
        raise ValueError("bug")

    with qtbot.waitSignal(worker.command_failed, timeout=WAIT_MS) as blocker:
        future = worker.run_in_thread(broken)
    assert blocker.args == ["device_timeout"]
    with pytest.raises(DeviceError):
        future.result(timeout=10)
    future = worker.run_in_thread(crashing)
    with pytest.raises(ValueError, match="bug"):
        future.result(timeout=10)
    qtbot.waitUntil(lambda: len(rec.command_failed) == 2, timeout=WAIT_MS)
    assert rec.command_failed == ["device_timeout", "device_io_failed"]
    assert worker.run_in_thread(lambda d: 42).result(timeout=10) == 42  # the worker keeps running
    assert rec.failed == []


def test_fail_next_read_emits_failed_and_the_thread_finishes(qtbot):
    device = mock()
    worker = make_worker(device)
    rec = Recorder(worker)
    device.fail_next_read("device_io_failed")
    with qtbot.waitSignal(worker.failed, timeout=WAIT_MS) as blocker:
        worker.start()
    assert blocker.args == ["device_io_failed"]
    assert worker.wait(5000) and worker.isFinished()
    assert rec.failed == ["device_io_failed"]
    # commands submitted after the end are cancelled instead of hanging
    with pytest.raises(CancelledError):
        worker.run_in_thread(lambda d: 1).result(timeout=5)


def test_a_device_error_key_is_passed_on(qtbot):
    device = mock()
    device.fail_next_read("device_timeout")
    worker = make_worker(device)
    with qtbot.waitSignal(worker.failed, timeout=WAIT_MS) as blocker:
        worker.start()
    assert blocker.args == ["device_timeout"]
    assert worker.wait(5000)


def test_unexpected_exception_becomes_device_io_failed(qtbot):
    class Crashing(MockGyroscope):
        def read(self, timeout_s):
            raise RuntimeError("bug in the adapter")

    worker = make_worker(Crashing())
    with qtbot.waitSignal(worker.failed, timeout=WAIT_MS) as blocker:
        worker.start()
    assert blocker.args == ["device_io_failed"]
    assert worker.wait(5000)


def test_abort_finishes_quickly_and_cancels_pending_commands(qtbot, qt_messages):
    device = mock()
    device.pause_stream(True)  # read() only sleeps
    worker = make_worker(device, read_timeout_s=0.05)
    gate = threading.Event()
    worker.start()
    blocking = worker.run_in_thread(lambda d: gate.wait(5))
    pending = worker.run_in_thread(lambda d: 1)
    qtbot.waitUntil(lambda: blocking.running(), timeout=WAIT_MS)
    started_at = time.monotonic()
    worker.abort()
    assert pending.cancelled()
    gate.set()
    assert worker.wait(1000)
    assert time.monotonic() - started_at < 1.0
    assert blocking.result(timeout=1) is True
    assert_no_thread_complaints(qt_messages)


def test_abort_with_a_blocking_read_is_noticed_within_one_read_timeout(qtbot, qt_messages):
    class SlowRead(MockGyroscope):
        def read(self, timeout_s):
            time.sleep(timeout_s)
            return []

    device = SlowRead(SimulationParams())
    device.open()
    worker = make_worker(device, read_timeout_s=0.1)
    worker.start()
    qtbot.wait(50)
    started_at = time.monotonic()
    worker.abort()
    assert worker.wait(1000)
    assert time.monotonic() - started_at < 1.0
    assert_no_thread_complaints(qt_messages)


def test_abort_before_start_ends_the_loop_at_once(qtbot):
    worker = make_worker(mock())
    worker.abort()
    worker.start()
    assert worker.wait(2000)


def test_stats_are_emitted_periodically(qtbot, started):
    worker = make_worker(mock(), stats_interval_s=0.05)
    rec = Recorder(worker)
    started(worker)
    qtbot.waitUntil(lambda: len(rec.stats) >= 3, timeout=WAIT_MS)
    assert rec.stats[-1].received >= rec.stats[0].received


# ---- end to end: worker + UDP device + fake firmware -----------------------------------------


@pytest.mark.parametrize("protocol_version", [1, 2])
def test_end_to_end_with_the_udp_device(qtbot, started, local_port, protocol_version):
    with FakeFirmware(protocol_version=protocol_version, data_port=local_port) as fake:
        device = UdpGyroDevice(
            LOCALHOST,
            fake.port,
            local_port,
            http_port=fake.http_port,
            info_timeout_s=0.5,
            bind_host=LOCALHOST,
        )
        device.open()
        worker = make_worker(device, data_timeout_s=1.0, lost_after_s=20.0)
        rec = Recorder(worker)
        try:
            started(worker)
            qtbot.waitUntil(lambda: rec.sample_count >= 100, timeout=WAIT_MS)
            assert rec.states[:2] == ["connecting", "connected"]
            expect_seq = protocol_version == 2
            seq = rec.batches[0].seq
            assert bool((seq >= 0).all()) is expect_seq

            fake.stop_sending()
            qtbot.waitUntil(lambda: "stale" in rec.states, timeout=WAIT_MS)
            before = rec.sample_count
            fake.resume()
            qtbot.waitUntil(lambda: rec.states[-1] == "connected", timeout=WAIT_MS)
            qtbot.waitUntil(lambda: rec.sample_count > before + 20, timeout=WAIT_MS)

            n = fake.registrations
            qtbot.waitUntil(lambda: fake.registrations > n + 1, timeout=WAIT_MS)  # keep-alive
            qtbot.waitUntil(lambda: bool(rec.stats) and rec.stats[-1].received > 0, timeout=WAIT_MS)
            assert rec.stats[-1].protocol_version == protocol_version
            assert rec.failed == []
        finally:
            worker.abort()
            worker.wait(5000)
            device.close()
