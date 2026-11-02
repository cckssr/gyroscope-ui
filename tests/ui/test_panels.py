"""The control panels: German texts from config.json, signals on clicks, no signals from the
``set_*`` methods, and the state-dependent texts and enabling."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QCheckBox, QLineEdit

from gyroscope_ui.core.models import DeviceInfo, LinkState
from gyroscope_ui.ui.widgets.connection_panel import ConnectionPanel
from gyroscope_ui.ui.widgets.live_panel import LivePanel
from gyroscope_ui.ui.widgets.measurement_panel import MeasurementPanel
from gyroscope_ui.ui.widgets.measurement_view import MeasurementView
from gyroscope_ui.ui.widgets.save_panel import SavePanel
from gyroscope_ui.ui.widgets.simulation_panel import SimulationPanel

LEFT = Qt.MouseButton.LeftButton
PANELS = [
    ConnectionPanel,
    LivePanel,
    MeasurementPanel,
    SavePanel,
    SimulationPanel,
]


def make(qtbot, cls, config):
    panel = cls()
    qtbot.addWidget(panel)
    panel.apply_config(config)
    return panel


@pytest.mark.parametrize("cls", PANELS)
def test_panel_fits_a_narrow_dock(qtbot, config, cls):
    panel = make(qtbot, cls, config)
    assert panel.minimumSizeHint().width() <= 320


@pytest.mark.parametrize("cls", [*PANELS, MeasurementView])
def test_apply_config_reports_no_unknown_objects(qtbot, config, caplog, cls):
    make(qtbot, cls, config)
    assert "unknown object" not in caplog.text


# ---- connection panel -----------------------------------------------------------------------
@pytest.mark.parametrize(
    ("state", "led"),
    [
        ("disconnected", "off"),
        ("connecting", "busy"),
        ("connected", "ok"),
        ("stale", "warning"),
        ("lost", "error"),
        ("error", "error"),
    ],
)
def test_connection_led_follows_the_link_state(qtbot, config, state, led):
    panel = make(qtbot, ConnectionPanel, config)
    panel.set_link(state, "Text")
    assert panel.ui.ledLink.state == led
    assert panel.ui.labelState.text() == "Text"


def test_connection_texts_are_german(qtbot, config):
    panel = make(qtbot, ConnectionPanel, config)
    assert panel.title() == "Gerät"
    assert panel.ui.checkSimulate.text() == "Simulation"
    assert panel.ui.buttonConnect.text() == "Verbinden"
    assert "Kreisel-*" in panel.ui.labelHint.text()
    assert "{ssid}" not in panel.ui.labelHint.text()
    assert panel.ui.labelHint.wordWrap()
    assert panel.ui.labelDevice.text() == "–"


def test_connection_button_emits_connect_or_disconnect_by_state(qtbot, config):
    panel = make(qtbot, ConnectionPanel, config)
    panel.show()
    connects = QSignalSpy(panel.connect_requested)
    disconnects = QSignalSpy(panel.disconnect_requested)
    for state, texts in [
        (LinkState.DISCONNECTED, "Verbinden"),
        (LinkState.ERROR, "Verbinden"),
        (LinkState.CONNECTING, "Trennen"),
        (LinkState.CONNECTED, "Trennen"),
        (LinkState.STALE, "Trennen"),
        (LinkState.LOST, "Trennen"),
    ]:
        panel.set_link(state.value, "x")
        assert panel.ui.buttonConnect.text() == texts
        qtbot.mouseClick(panel.ui.buttonConnect, LEFT)
    assert (connects.count(), disconnects.count()) == (2, 4)


def test_connection_set_link_rejects_unknown_states(qtbot, config):
    panel = make(qtbot, ConnectionPanel, config)
    with pytest.raises(ValueError):
        panel.set_link("bogus", "x")


def test_connection_device_text(qtbot, config):
    panel = make(qtbot, ConnectionPanel, config)
    panel.set_device(
        DeviceInfo("E35433", "192.168.4.1:12345", firmware_version="1.1.1", protocol_version=1)
    )
    assert panel.ui.labelDevice.text() == "E35433 · Firmware 1.1.1 · Protokoll 1"
    panel.set_device(DeviceInfo("E35433", "192.168.4.1:12345"))
    assert panel.ui.labelDevice.text() == "E35433 · Firmware ? · Protokoll ?"
    panel.set_device(None)
    assert panel.ui.labelDevice.text() == "–"


def test_connection_simulation_switch(qtbot, config):
    panel = make(qtbot, ConnectionPanel, config)
    panel.show()
    spy = QSignalSpy(panel.simulate_toggled)
    panel.set_simulate(True)
    assert panel.ui.checkSimulate.isChecked()
    assert spy.count() == 0
    # The check box spans the panel; only its indicator and text react to the mouse.
    qtbot.mouseClick(
        panel.ui.checkSimulate, LEFT, pos=QPoint(8, panel.ui.checkSimulate.height() // 2)
    )
    assert spy.count() == 1 and spy.at(0) == [False]
    panel.set_simulate_enabled(False)
    assert not panel.ui.checkSimulate.isEnabled()


def test_connection_keeps_the_link_text_across_apply_config(qtbot, config):
    panel = make(qtbot, ConnectionPanel, config)
    panel.set_link("connected", "Verbunden")
    panel.apply_config(config)
    assert panel.ui.labelState.text() == "Verbunden"
    assert panel.ui.buttonConnect.text() == "Trennen"


# ---- live panel -----------------------------------------------------------------------------
def test_live_panel_formats_values(qtbot, config):
    panel = make(qtbot, LivePanel, config)
    assert panel.title() == "Live-Messwerte"
    panel.show_values(12.3456, -0.12345)
    assert panel.displayed["frequency"] == "12.35"
    assert panel.displayed["gyro_z"] == "-0.123"
    assert panel.ui.lcdFrequency.value() == pytest.approx(12.35)
    assert panel.ui.lcdGyroZ.value() == pytest.approx(-0.123)


def test_live_panel_blank_values(qtbot, config):
    panel = make(qtbot, LivePanel, config)
    panel.show_values(1.0, 2.0)
    panel.show_values(None, float("nan"))
    assert panel.displayed["frequency"] == "--"
    assert panel.displayed["gyro_z"] == "--"


def test_live_panel_recording_counters(qtbot, config):
    panel = make(qtbot, LivePanel, config)
    panel.show_recording(1234, 125.9)
    assert panel.ui.lcdPoints.value() == 1234
    assert panel.ui.labelDuration.text() == "02:05"
    panel.show_recording(5, 3600.0)
    assert panel.ui.labelDuration.text() == "60:00"
    panel.clear()
    assert panel.ui.labelDuration.text() == "00:00"
    assert panel.displayed == {"frequency": "--", "gyro_z": "--", "points": "0"}


# ---- measurement panel ----------------------------------------------------------------------
def test_measurement_panel_texts_and_enabling_per_state(qtbot, config):
    panel = make(qtbot, MeasurementPanel, config)
    ui = panel.ui
    assert panel.title() == "Messung"
    expected = {
        # state: (start/stop text, state text, start/stop enabled once can_start, reset enabled)
        "empty": ("Start", "Bereit", True, False),
        "recording": ("Stop", "Messung läuft", True, False),
        "stopped": ("Start", "Gestoppt, nicht gespeichert", True, True),
        "saved": ("Start", "Gespeichert", True, True),
    }
    for state, (button, text, enabled, reset) in expected.items():
        panel.set_can_start(True)
        panel.set_state(state)
        assert ui.buttonStartStop.text() == button, state
        assert ui.labelState.text() == text, state
        assert ui.buttonStartStop.isEnabled() is enabled, state
        assert ui.buttonReset.isEnabled() is reset, state


def test_measurement_start_needs_can_start_but_stop_is_always_possible(qtbot, config):
    panel = make(qtbot, MeasurementPanel, config)
    panel.set_can_start(False)
    for state in ("empty", "stopped", "saved"):
        panel.set_state(state)
        assert not panel.ui.buttonStartStop.isEnabled(), state
    panel.set_state("recording")
    assert panel.ui.buttonStartStop.isEnabled()
    panel.set_state("stopped")
    panel.set_can_start(True)
    assert panel.ui.buttonStartStop.isEnabled()


def test_measurement_signals_and_unknown_state(qtbot, config):
    panel = make(qtbot, MeasurementPanel, config)
    panel.show()
    panel.set_can_start(True)
    panel.set_state("stopped")
    start_stop = QSignalSpy(panel.start_stop_requested)
    reset = QSignalSpy(panel.reset_requested)
    qtbot.mouseClick(panel.ui.buttonStartStop, LEFT)
    qtbot.mouseClick(panel.ui.buttonReset, LEFT)
    assert (start_stop.count(), reset.count()) == (1, 1)
    with pytest.raises(ValueError):
        panel.set_state("bogus")


# ---- save panel -----------------------------------------------------------------------------
def test_save_panel_texts(qtbot, config):
    panel = make(qtbot, SavePanel, config)
    ui = panel.ui
    assert panel.title() == "Speichern"
    assert ui.buttonSave.text() == "Speichern …"
    assert ui.checkAutoSave.text() == "Automatisch speichern"
    assert "*" in ui.captionGroup.text() and "*" in ui.captionSubgroup.text()
    assert "*" not in ui.captionSuffix.text()
    assert "JJJJ_MM_TT" in ui.checkAutoSave.toolTip()
    assert ui.editSubgroup.toolTip()
    assert ui.comboGroup.count() == 26 and ui.comboGroup.itemText(25) == "Z"
    assert ui.editDataDir.isReadOnly()
    assert ui.labelLastSaved.text() == "–"
    assert not ui.buttonSave.isEnabled()


def test_save_panel_signals(qtbot, config):
    panel = make(qtbot, SavePanel, config)
    panel.show()
    ui = panel.ui
    groups, subgroups = QSignalSpy(panel.group_changed), QSignalSpy(panel.subgroup_changed)
    suffixes, autos = QSignalSpy(panel.suffix_changed), QSignalSpy(panel.auto_save_toggled)
    saves, browses = QSignalSpy(panel.save_requested), QSignalSpy(panel.browse_requested)
    ui.comboGroup.setCurrentIndex(2)
    qtbot.keyClicks(ui.editSubgroup, "Aufbau 1")
    qtbot.keyClicks(ui.editSuffix, "a")
    qtbot.mouseClick(ui.checkAutoSave, LEFT)
    panel.set_can_save(True)
    qtbot.mouseClick(ui.buttonSave, LEFT)
    qtbot.mouseClick(ui.buttonBrowse, LEFT)
    assert groups.count() == 1 and groups.at(0) == ["C"]
    assert subgroups.at(subgroups.count() - 1) == ["Aufbau 1"]
    assert suffixes.at(0) == ["a"]
    assert autos.count() == 1
    assert (saves.count(), browses.count()) == (1, 1)


def test_save_panel_set_values_roundtrips_without_emitting(qtbot, config):
    panel = make(qtbot, SavePanel, config)
    spies = [
        QSignalSpy(signal)
        for signal in (
            panel.group_changed,
            panel.subgroup_changed,
            panel.suffix_changed,
            panel.auto_save_toggled,
        )
    ]
    panel.set_values("F", "Aufbau 2", "test", "/tmp/Kreisel", True)
    ui = panel.ui
    assert ui.comboGroup.currentText() == "F"
    assert ui.editSubgroup.text() == "Aufbau 2"
    assert ui.editSuffix.text() == "test"
    assert ui.editDataDir.text() == "/tmp/Kreisel"
    assert "/tmp/Kreisel" in ui.editDataDir.toolTip()
    assert ui.checkAutoSave.isChecked()
    assert [spy.count() for spy in spies] == [0, 0, 0, 0]


def test_save_panel_inputs_and_save_enabling(qtbot, config):
    panel = make(qtbot, SavePanel, config)
    ui = panel.ui
    panel.set_inputs_enabled(False)
    for widget in (ui.comboGroup, ui.editSubgroup, ui.editSuffix, ui.buttonBrowse):
        assert not widget.isEnabled()
    assert ui.checkAutoSave.isEnabled()
    panel.set_inputs_enabled(True)
    assert ui.comboGroup.isEnabled() and ui.buttonBrowse.isEnabled()
    panel.set_can_save(True)
    assert ui.buttonSave.isEnabled()


def test_save_panel_last_saved(qtbot, config):
    panel = make(qtbot, SavePanel, config)
    panel.set_last_saved("/data/A_Aufbau/2026_11_02-01-Messung.csv")
    assert panel.ui.labelLastSaved.text() == "/data/A_Aufbau/2026_11_02-01-Messung.csv"
    panel.set_last_saved(None)
    assert panel.ui.labelLastSaved.text() == "–"


def test_save_panel_mark_missing(qtbot, config):
    panel = make(qtbot, SavePanel, config)
    ui = panel.ui
    panel.mark_missing({"group", "subgroup"})
    assert ui.comboGroup.property("missing") is True
    assert ui.editSubgroup.property("missing") is True
    panel.mark_missing({"subgroup"})
    assert not ui.comboGroup.property("missing")
    assert ui.editSubgroup.property("missing") is True
    panel.mark_missing(set())
    assert not ui.editSubgroup.property("missing")
    assert "missing" in panel.styleSheet()


def test_save_panel_mark_is_cleared_by_typing(qtbot, config):
    panel = make(qtbot, SavePanel, config)
    panel.show()
    panel.mark_missing({"subgroup"})
    qtbot.keyClicks(panel.ui.editSubgroup, "A")
    assert not panel.ui.editSubgroup.property("missing")


def test_save_panel_widgets_are_the_documented_types(qtbot, config):
    panel = make(qtbot, SavePanel, config)
    assert isinstance(panel.ui.editSubgroup, QLineEdit)
    assert isinstance(panel.ui.checkAutoSave, QCheckBox)


# ---- simulation panel -----------------------------------------------------------------------
def test_simulation_panel(qtbot, config):
    panel = make(qtbot, SimulationPanel, config)
    panel.show()
    ui = panel.ui
    assert panel.title() == "Simulation"
    assert ui.buttonKick.text() == "Anwerfen"
    assert ui.spinStartFrequency.suffix() == " Hz"
    assert (ui.spinStartFrequency.minimum(), ui.spinStartFrequency.maximum()) == (1.0, 60.0)
    assert ui.spinStartFrequency.value() == 15.0
    spy = QSignalSpy(panel.kick_requested)
    ui.spinStartFrequency.setValue(22.5)
    qtbot.mouseClick(ui.buttonKick, LEFT)
    assert spy.count() == 1 and spy.at(0) == [22.5]


def test_simulation_default_comes_from_the_config(qtbot, config):
    panel = make(
        qtbot, SimulationPanel, config.with_overrides({"simulation": {"start_frequency_hz": 8.0}})
    )
    assert panel.ui.spinStartFrequency.value() == 8.0
    panel = make(
        qtbot, SimulationPanel, config.with_overrides({"simulation": {"start_frequency_hz": 500.0}})
    )
    assert panel.ui.spinStartFrequency.value() == 60.0


# ---- measurement view -----------------------------------------------------------------------
def test_measurement_view_defaults_and_texts(qtbot, config):
    view = make(qtbot, MeasurementView, config)
    ui = view.ui
    assert ui.checkAutoScroll.text() == "Auto-Scroll"
    assert ui.checkAllChannels.text() == "Alle Kanäle"
    assert ui.buttonAutoRange.text() == "Auto-Range"
    assert ui.spinScrollWindow.suffix() == " s"
    assert (ui.spinScrollWindow.minimum(), ui.spinScrollWindow.maximum()) == (5, 3600)
    assert ui.checkAutoScroll.isChecked() and ui.spinScrollWindow.value() == 60
    assert not ui.checkAllChannels.isChecked()
    assert view.plot is ui.plot


def test_measurement_view_signals_and_plot(qtbot, config):
    view = make(qtbot, MeasurementView, config)
    view.show()
    ui = view.ui
    scrolls, channels = QSignalSpy(view.auto_scroll_changed), QSignalSpy(view.all_channels_toggled)
    ranges = QSignalSpy(view.auto_range_requested)
    qtbot.mouseClick(ui.checkAllChannels, LEFT)
    assert channels.at(0) == [True] and view.plot.all_channels
    ui.spinScrollWindow.setValue(30)
    assert scrolls.at(scrolls.count() - 1) == [True, 30.0]
    qtbot.mouseClick(ui.checkAutoScroll, LEFT)
    assert scrolls.at(scrolls.count() - 1) == [False, 30.0]
    assert not ui.spinScrollWindow.isEnabled()
    calls = []
    view.plot.auto_range = lambda: calls.append(1)  # type: ignore[method-assign]
    qtbot.mouseClick(ui.buttonAutoRange, LEFT)
    assert ranges.count() == 1 and calls == [1]


def test_measurement_view_set_options_does_not_emit(qtbot, config):
    view = make(qtbot, MeasurementView, config)
    spies = [QSignalSpy(s) for s in (view.auto_scroll_changed, view.all_channels_toggled)]
    view.set_options(False, 120.0, True)
    assert [s.count() for s in spies] == [0, 0]
    ui = view.ui
    assert not ui.checkAutoScroll.isChecked() and ui.spinScrollWindow.value() == 120
    assert ui.checkAllChannels.isChecked() and view.plot.all_channels
