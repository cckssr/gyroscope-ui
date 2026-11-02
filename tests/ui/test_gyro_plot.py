"""GyroPlot: data handling, speed, channel visibility, auto-scroll range, texts and colours."""

from __future__ import annotations

import time

import numpy as np
import pytest
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from gyroscope_ui.core.models import CHANNELS
from gyroscope_ui.ui.widgets.gyro_plot import GyroPlot


@pytest.fixture
def plot(qtbot, config) -> GyroPlot:
    widget = GyroPlot()
    qtbot.addWidget(widget)
    widget.apply_config(config)
    widget.resize(800, 600)
    widget.show()
    return widget


def columns(n: int, t: np.ndarray | None = None) -> dict[str, np.ndarray]:
    t = np.arange(n) / 100.0 if t is None else t
    return {name: np.sin(t * (i + 1)) for i, name in enumerate(CHANNELS)}


def shown(curve) -> int:
    x, _y = curve.getData()
    return 0 if x is None else len(x)


def test_default_channels_only(plot):
    n = 1000
    plot.set_data(np.arange(n) / 100.0, columns(n))
    for name in ("frequency_hz", "gyro_z_rad_s"):
        assert plot.curves[name].isVisible()
        assert plot.curves[name].xData is not None and len(plot.curves[name].xData) == n
    for name in CHANNELS:
        if name not in ("frequency_hz", "gyro_z_rad_s"):
            assert not plot.curves[name].isVisible()
            assert plot.curves[name].xData is None or len(plot.curves[name].xData) == 0
    assert not plot.accel_plot.isVisible()
    assert plot.accel_plot not in plot.ci.items


def test_all_channels_show_the_extra_curves_and_the_third_plot(plot):
    n = 500
    t = np.arange(n) / 100.0
    plot.set_data(t, columns(n))
    plot.set_all_channels(True)  # the stored data are drawn without a new set_data call
    assert plot.all_channels
    for curve in plot.curves.values():
        assert curve.isVisible() and len(curve.xData) == n
    assert plot.accel_plot.isVisible() and plot.accel_plot in plot.ci.items
    plot.set_all_channels(False)
    assert not plot.accel_plot.isVisible() and plot.accel_plot not in plot.ci.items
    assert not plot.curves["accel_x_m_s2"].isVisible()
    plot.set_all_channels(True)  # can be shown again
    assert plot.accel_plot in plot.ci.items


def test_big_data_set_is_fast(plot, qtbot):
    n = 360_000
    t = np.arange(n) / 100.0
    data = columns(n, t)
    start = time.perf_counter()
    plot.set_data(t, data)
    qtbot.wait(1)  # let a repaint run
    assert time.perf_counter() - start < 1.0
    plot.set_all_channels(True)
    start = time.perf_counter()
    plot.set_data(t, data)
    qtbot.wait(1)
    assert time.perf_counter() - start < 2.0


def test_empty_and_nan_data(plot, qtbot):
    plot.set_data(np.empty(0), {name: np.empty(0) for name in CHANNELS})
    plot.set_data(np.empty(0), {})
    t = np.arange(100) / 100.0
    data = columns(100, t)
    data["frequency_hz"][10:20] = np.nan
    data["gyro_z_rad_s"][:] = np.nan
    plot.set_data(t, data)
    plot.set_all_channels(True)
    plot.set_data(t, data)
    qtbot.wait(1)
    plot.set_data(t, {"frequency_hz": data["frequency_hz"]})  # missing channels are cleared
    assert shown(plot.curves["gyro_z_rad_s"]) == 0


def test_length_mismatch_is_rejected(plot):
    with pytest.raises(ValueError):
        plot.set_data(np.arange(10.0), {"frequency_hz": np.arange(9.0)})


def test_auto_scroll_follows_the_newest_time(plot):
    plot.set_auto_scroll(True, 10.0)
    t = np.arange(0, 100, 0.1)
    plot.set_data(t, columns(len(t), t))
    left, right = plot.x_range()
    assert right == pytest.approx(t[-1]) and left == pytest.approx(t[-1] - 10.0)
    t2 = np.arange(0, 200, 0.1)
    plot.set_data(t2, columns(len(t2), t2))
    assert plot.x_range() == pytest.approx((t2[-1] - 10.0, t2[-1]))
    for item in (plot.frequency_plot, plot.gyro_plot):
        assert item.getViewBox().viewRange()[0] == pytest.approx([t2[-1] - 10.0, t2[-1]])
    plot.set_auto_scroll(True, 20.0)  # a new window width applies at once
    assert plot.x_range() == pytest.approx((t2[-1] - 20.0, t2[-1]))


def test_auto_scroll_off_restores_interactive_zoom(plot):
    plot.set_auto_scroll(True, 10.0)
    assert plot.frequency_plot.getViewBox().state["mouseEnabled"][0] is False
    plot.set_auto_scroll(False, 10.0)
    assert plot.frequency_plot.getViewBox().state["mouseEnabled"][0] is True
    t = np.arange(0, 100, 0.1)
    plot.set_data(t, columns(len(t), t))
    plot.frequency_plot.setXRange(10, 20, padding=0)
    plot.set_data(t, columns(len(t), t))
    assert plot.x_range() == pytest.approx((10, 20))  # data do not move the range any more


def test_auto_range_shows_everything_again(plot, qtbot):
    t = np.arange(0, 100, 0.1)
    plot.set_data(t, columns(len(t), t))
    plot.frequency_plot.setXRange(10, 20, padding=0)
    plot.auto_range()
    # pyqtgraph recomputes the bounds on the next repaint (clip-to-view is off while autorange runs)
    qtbot.waitUntil(lambda: plot.x_range()[0] <= t[0] and plot.x_range()[1] >= t[-1], timeout=2000)
    assert plot.frequency_plot.getViewBox().state["autoRange"][0]
    assert plot.gyro_plot.getViewBox().state["autoRange"][1]


def test_auto_range_keeps_the_time_axis_while_scrolling(plot):
    t = np.arange(0, 100, 0.1)
    plot.set_auto_scroll(True, 10.0)
    plot.set_data(t, columns(len(t), t))
    plot.auto_range()
    assert plot.x_range() == pytest.approx((t[-1] - 10.0, t[-1]))


def test_clear_empties_the_curves(plot):
    t = np.arange(0, 10, 0.1)
    plot.set_data(t, columns(len(t), t))
    plot.set_auto_scroll(True, 30.0)
    plot.clear()
    assert all(shown(curve) == 0 for curve in plot.curves.values())
    assert plot.x_range() == pytest.approx((0.0, 30.0))
    plot.set_auto_scroll(False, 30.0)
    plot.clear()  # does not raise without a stored data set


def test_texts_come_from_the_config(plot):
    assert plot.frequency_plot.titleLabel.text == "Rotationsfrequenz Scheibe"
    assert plot.gyro_plot.getAxis("left").labelText == "Winkelgeschwindigkeit (rad/s)"
    assert plot.accel_plot.getAxis("left").labelText == "Beschleunigung (m/s²)"
    assert plot.gyro_plot.getAxis("bottom").labelText == "Vergangene Zeit (s)"
    # With two plots the time axis is labelled once, under the lowest one.
    assert not plot.frequency_plot.getAxis("bottom").label.isVisible()
    plot.set_x_label("Zeit (s)")
    assert plot.gyro_plot.getAxis("bottom").labelText == "Zeit (s)"
    plot.set_all_channels(True)
    assert plot.accel_plot.getAxis("bottom").labelText == "Zeit (s)"
    assert not plot.gyro_plot.getAxis("bottom").label.isVisible()


def test_legend_lists_only_visible_curves(plot):
    legend = plot._legends["gyro"]
    assert [label.text for _sample, label in legend.items] == ["ω_z"]
    plot.set_all_channels(True)
    assert [label.text for _sample, label in legend.items] == ["ω_x", "ω_y", "ω_z"]


def test_lines_only_downsampled_and_clipped(plot):
    curve = plot.curves["frequency_hz"]
    assert curve.opts["symbol"] is None
    assert curve.opts["autoDownsample"] is True
    assert curve.opts["downsampleMethod"] == "peak"
    assert curve.opts["clipToView"] is True


def test_background_and_pens_follow_the_palette(plot):
    palette = QPalette(plot.palette())
    palette.setColor(QPalette.ColorRole.Base, QColor("#202020"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    plot.setPalette(palette)
    assert plot.backgroundBrush().color() == QColor("#202020")
    pen = plot.frequency_plot.getAxis("left").pen()
    assert pen.color() == QColor("#e0e0e0")
    x_color = plot.curves["gyro_x_rad_s"].opts["pen"].color()
    assert x_color.value() > 200  # brighter curves on a dark background


def test_auto_scroll_short_data_has_no_empty_stretch(plot):
    """A fresh recording fills the window from 0; the preview (t <= 0) shows just its data."""
    plot.set_auto_scroll(True, 60.0)
    t = np.linspace(0.0, 15.0, 1500)
    plot.set_data(t, columns(len(t), t))
    assert plot.x_range() == pytest.approx((0.0, 60.0))
    t = np.linspace(-30.0, 0.0, 3000)
    plot.set_data(t, columns(len(t), t))
    assert plot.x_range() == pytest.approx((-30.0, 0.0))


# ---- cursor ---------------------------------------------------------------------------------
def scene_pos(plot: GyroPlot, key: str, x: float, y: float):
    """Scene position of the view point (x, y) once the layout and the ranges have settled."""
    QApplication.processEvents()
    plot.frequency_plot.setXRange(0.0, 10.0, padding=0)
    vb = plot._plots[key].getViewBox()
    vb.setYRange(-1.0, 1.0, padding=0)
    return vb.mapViewToScene(QPointF(x, y))


def test_cursor_is_hidden_until_the_mouse_is_over_a_plot(plot):
    plot.set_data(np.arange(1000) / 100.0, columns(1000))
    assert not any(line.isVisible() for line in plot._vlines.values())
    plot._on_mouse_moved(QPointF(-100.0, -100.0))
    assert not any(line.isVisible() for line in plot._vlines.values())


def test_cursor_crosshair_in_the_hovered_plot_and_vertical_line_in_all(plot):
    plot.set_data(np.arange(1000) / 100.0, columns(1000))
    plot.set_all_channels(True)
    plot._on_mouse_moved(scene_pos(plot, "gyro", 4.0, 0.5))
    assert all(plot._vlines[key].isVisible() for key in ("frequency", "gyro", "accel"))
    assert all(plot._vlines[key].value() == pytest.approx(4.0) for key in plot._vlines)
    assert plot._hlines["gyro"].isVisible() and plot._hlines["gyro"].value() == pytest.approx(0.5)
    assert not plot._hlines["frequency"].isVisible() and not plot._hlines["accel"].isVisible()
    assert plot._readouts["gyro"].isVisible() and not plot._readouts["frequency"].isVisible()
    text = plot._readouts["gyro"].toPlainText()
    assert "t = 4.00 s" in text and "0.5 rad/s" in text
    plot._hide_cursor()
    assert not any(line.isVisible() for line in plot._vlines.values())


def test_cursor_ignores_the_accel_plot_while_it_is_hidden(plot):
    plot.set_data(np.arange(1000) / 100.0, columns(1000))
    plot._on_mouse_moved(scene_pos(plot, "frequency", 2.0, 0.0))
    assert not plot._vlines["accel"].isVisible()


def test_cursor_does_not_change_the_auto_range(plot):
    n = 500
    plot.set_data(np.arange(n) / 100.0, columns(n))
    plot.set_auto_scroll(False, 60.0)
    plot.auto_range()
    QApplication.processEvents()
    before = plot.frequency_plot.getViewBox().viewRange()
    plot._on_mouse_moved(plot.frequency_plot.getViewBox().sceneBoundingRect().center())
    assert plot._vlines["frequency"].isVisible()
    plot.auto_range()
    QApplication.processEvents()
    assert plot.frequency_plot.getViewBox().viewRange() == before
