"""Main window assembly, actions, layout on small screens and shutdown."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from PySide6.QtWidgets import QApplication
from ui_helpers import connect, record

from gyroscope_ui import __version__
from gyroscope_ui.ui.windows.main_window import CANCEL, SAVE

SCREEN_WIDTH, SCREEN_HEIGHT, NARROW_SCREEN_WIDTH = 1366, 768, 1024


@pytest.fixture
def qt_messages():
    """Qt log messages emitted during the test."""
    messages: list[str] = []

    def handler(_mode: QtMsgType, _context, text: str) -> None:
        messages.append(text)

    previous = qInstallMessageHandler(handler)
    yield messages
    qInstallMessageHandler(previous)


def test_window_parts(window):
    assert __version__ in window.windowTitle()
    assert window.ui.tabs.count() == 1 and window.ui.tabs.tabText(0) == "Messung"
    assert window.simulation_panel.isVisibleTo(window)  # simulate=True
    assert "(" in window.ui.actionSave.toolTip()  # shortcut hint appended
    assert not window.ui.actionSave.isEnabled()


def test_actions_follow_state(qtbot, connected):
    ui = connected.ui
    assert ui.actionConnect.text() == "Trennen"
    assert ui.actionStartStop.isEnabled()
    ui.actionStartStop.trigger()
    assert ui.actionStartStop.text() == "Stop"
    record_wait = connected.context.measurement
    qtbot.waitUntil(lambda: len(record_wait.recording) > 5)
    ui.actionStartStop.trigger()
    assert ui.actionSave.isEnabled()
    ui.actionConnect.trigger()
    assert connected.context.connection.state == "disconnected"


def test_status_bar_rate(qtbot, connected):
    label = connected._label_rate
    qtbot.waitUntil(lambda: not label.text().startswith("–"), timeout=5_000)
    assert label.text().endswith("Messwerte/s")


def test_plot_shows_preview_then_recording(qtbot, connected):
    plot = connected.tabs["measurement"].plot

    def x_data():
        x = plot.curves["frequency_hz"].getData()[0]
        return x if x is not None else []

    qtbot.waitUntil(lambda: len(x_data()) > 0)
    assert max(x_data()) <= 0.0  # time relative to now
    record(qtbot, connected, samples=30)
    qtbot.waitUntil(lambda: len(x_data()) > 0 and max(x_data()) > 0)


def _feed_preview(window, seconds: int) -> None:
    from gyroscope_ui.core.models import Sample, SampleBatch

    samples = [
        Sample(
            device_ms=i * 10,
            frequency_hz=1.0,
            accel_x_m_s2=0.0,
            accel_y_m_s2=0.0,
            accel_z_m_s2=9.81,
            gyro_x_rad_s=0.0,
            gyro_y_rad_s=0.0,
            gyro_z_rad_s=1.0,
            seq=i,
            host_time_s=i / 100.0,
        )
        for i in range(seconds * 100)
    ]
    window.context.measurement.preview.extend(SampleBatch.from_samples(samples))


def test_preview_reaches_back_as_far_as_the_scroll_window(window):
    tab = window.tabs["measurement"]
    tab.view.ui.spinScrollWindow.setValue(90)  # longer than display.preview_s (30 s)
    _feed_preview(window, 120)
    tab.redraw()
    x = tab.plot.curves["frequency_hz"].xData
    assert x is not None and x.max() == 0.0
    assert -90.0 <= x.min() < -89.0
    left, right = tab.plot.x_range()
    assert right - left == pytest.approx(90.0)
    tab.view.ui.spinScrollWindow.setValue(10)  # back to the preview length
    tab.redraw()
    x = tab.plot.curves["frequency_hz"].xData
    assert -30.0 <= x.min() < -29.0


def test_fits_small_screens(window):
    hint = window.minimumSizeHint()
    assert hint.width() <= SCREEN_WIDTH and hint.height() <= SCREEN_HEIGHT
    window.ui.dockControls.hide()
    assert window.minimumSizeHint().width() <= NARROW_SCREEN_WIDTH
    window.ui.dockControls.show()
    scroll = window.ui.scrollControls
    assert scroll.horizontalScrollBarPolicy().name == "ScrollBarAlwaysOff"


def test_close_asks_for_unsaved_data(qtbot, connected):
    connected.show()
    record(qtbot, connected)
    connected.ask_unsaved_on_close = lambda: CANCEL
    connected.close()
    assert connected.isVisible() and not connected._shut_down
    assert connected.context.measurement.is_recording  # Cancel keeps the recording running
    connected.context.save.ask_save_path = lambda _d, _n: None
    connected.ask_unsaved_on_close = lambda: SAVE
    connected.context.session.update_save_fields(group="A", subgroup="x")
    connected.close()  # the save dialog was cancelled -> stay open
    assert connected.isVisible()


def test_close_while_recording_joins_threads(qtbot, connected, qt_messages):
    record(qtbot, connected)
    connected.close()
    assert connected._shut_down
    assert connected.context.connection.state == "disconnected"
    assert not any("Destroyed while thread" in m for m in qt_messages)


def test_shutdown_is_idempotent_and_runs_on_about_to_quit(qtbot, make_window, qt_messages):
    from gyroscope_ui.main import install_cleanup

    window = make_window()
    connect(qtbot, window)
    install_cleanup(QApplication.instance(), window)
    QApplication.instance().aboutToQuit.emit()
    assert window._shut_down
    window.shutdown()
    assert not any("Destroyed while thread" in m for m in qt_messages)
    QApplication.instance().aboutToQuit.disconnect(window.shutdown)
