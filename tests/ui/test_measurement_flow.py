"""Start / Stop / Reset in the simulation (CONCEPT 4.2) and the connection behind it."""

from __future__ import annotations

from PySide6.QtCore import Qt
from ui_helpers import connect, record

from gyroscope_ui.infrastructure.devices.base import DevicePortInUseError
from gyroscope_ui.infrastructure.mocks.mock_gyroscope import MockGyroscope


def test_start_needs_data(window):
    m = window.context.measurement
    assert not m.can_start
    assert not m.start()
    assert m.state == "empty"
    assert "Daten" in window.message_log[-1][1]


def test_start_stop_reset(qtbot, connected):
    m = connected.context.measurement
    record(qtbot, connected)
    assert m.state == "recording"
    assert connected.measurement_panel.ui.buttonStartStop.text() == "Stop"
    assert not connected.save_panel.ui.comboGroup.isEnabled()
    assert m.stop()
    assert m.state == "stopped" and m.has_unsaved and m.can_save
    n = len(m.recording)
    qtbot.wait(100)
    assert len(m.recording) == n  # nothing recorded after Stop
    elapsed = m.recording.column("elapsed_s")
    assert elapsed[0] == 0.0 and (elapsed[1:] > elapsed[:-1]).all()
    assert m.reset()
    assert m.state == "empty" and len(m.recording) == 0


def test_start_again_asks_before_discarding(qtbot, connected):
    m = connected.context.measurement
    record(qtbot, connected)
    m.stop()
    questions = []
    m.confirm = lambda text: questions.append(text) or False
    assert not m.start()
    assert m.state == "stopped" and len(questions) == 1
    assert not m.reset()
    m.confirm = lambda _text: True
    assert m.start()
    assert m.state == "recording"


def test_recording_limit_stops(qtbot, make_window, config):
    window = make_window(config.with_overrides({"storage": {"recording_limit_s": 0.3}}))
    connect(qtbot, window)
    m = window.context.measurement
    m.start()
    qtbot.waitUntil(lambda: m.state == "stopped", timeout=10_000)
    assert m.recording.duration_s >= 0.3
    assert any("Maximale Aufnahmedauer" in text for _level, text in window.message_log)


def test_live_values_shown(qtbot, connected):
    qtbot.waitUntil(lambda: connected.live_panel.displayed["frequency"] not in ("", "--"))
    assert float(connected.live_panel.displayed["frequency"].replace(",", ".")) > 0


def test_space_and_escape(qtbot, connected):
    m = connected.context.measurement
    connected.activateWindow()
    connected.ui.tabs.setFocus()
    qtbot.keyClick(connected.ui.tabs, Qt.Key.Key_Space)
    assert m.state == "recording"
    qtbot.keyClick(connected.ui.tabs, Qt.Key.Key_Escape)
    assert m.state == "stopped"


def test_space_types_in_text_field(qtbot, connected):
    m = connected.context.measurement
    edit = connected.save_panel.ui.editSubgroup
    edit.setFocus()
    qtbot.keyClick(edit, Qt.Key.Key_Space)
    assert m.state == "empty"


def test_reconnect_does_not_duplicate_batches(qtbot, connected):
    """D2: after disconnect + connect every batch arrives exactly once."""
    conn = connected.context.connection
    conn.disconnect_device()
    assert conn.state == "disconnected"
    connect(qtbot, connected)
    first_ms: list[int] = []
    conn.samples_ready.connect(lambda batch: first_ms.append(int(batch.device_ms[0])))
    record(qtbot, connected, samples=50)
    assert len(first_ms) == len(set(first_ms))  # no batch delivered twice
    rec = connected.context.measurement.recording
    device_ms = rec.column("device_ms")
    assert len(set(device_ms.tolist())) == len(device_ms)  # no sample twice


def test_simulation_switch_only_while_disconnected(qtbot, connected):
    conn = connected.context.connection
    conn.set_simulate(False)
    assert conn.simulate
    assert connected.connection_panel.ui.checkSimulate.isChecked()
    conn.disconnect_device()
    conn.set_simulate(False)
    assert not conn.simulate
    assert not connected.simulation_panel.isVisibleTo(connected)


def test_open_failure_shows_message_and_allows_retry(qtbot, make_window):
    def failing(_cfg, _simulate):
        raise DevicePortInUseError(port=12345)

    window = make_window(device_factory=failing)
    conn = window.context.connection
    conn.connect_device()
    assert conn.state == "error"
    assert "12345" in window.message_log[-1][1]
    assert window.connection_panel.ui.buttonConnect.text() == "Verbinden"


def test_worker_failure_ends_in_error(qtbot, make_window, config):
    devices: list[MockGyroscope] = []

    def factory(_cfg, _simulate):
        devices.append(MockGyroscope(time_scale=0.1))
        return devices[-1]

    window = make_window(device_factory=factory)
    connect(qtbot, window)
    devices[0].fail_next_read()
    conn = window.context.connection
    qtbot.waitUntil(lambda: conn.state == "error", timeout=5_000)
    assert not conn.is_attached
    connect(qtbot, window)  # a new attempt works without a restart
    assert conn.state == "connected"


def test_stale_and_recovered(qtbot, make_window):
    devices: list[MockGyroscope] = []

    def factory(_cfg, _simulate):
        devices.append(MockGyroscope(time_scale=0.1))
        return devices[-1]

    window = make_window(device_factory=factory)
    connect(qtbot, window)
    conn = window.context.connection
    record(qtbot, window)
    devices[0].pause_stream(True)
    qtbot.waitUntil(lambda: conn.state == "lost", timeout=5_000)
    assert window.context.measurement.is_recording  # recording continues through a gap
    devices[0].pause_stream(False)
    qtbot.waitUntil(lambda: conn.state == "connected", timeout=5_000)
    texts = [text for _level, text in window.message_log]
    assert any("abgerissen" in t for t in texts)
    assert any("wiederhergestellt" in t for t in texts)
