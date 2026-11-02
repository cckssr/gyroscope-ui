"""Plots of a measurement (pyqtgraph): rotation frequency over time on top, angular rate below,
and the acceleration as a third plot that exists only with "Alle Kanäle".

The plots sit in a vertical splitter, so their heights can be changed by dragging the dividers.
The x axes are linked. All curves are created once and updated with ``setData``; nothing loops
over points in Python (downsampling and clipping to the view are pyqtgraph's, ``peak`` mode keeps
spikes visible). Non-finite values leave gaps. Background and text follow the palette, so the plots
follow light and dark mode.

Every plot has a cursor that follows the curves: a vertical line at the sample nearest to the
mouse (in all visible plots at once), a marker on each curve and a read-out with the time and the
values of that sample.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QEvent, QPointF, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QSplitter, QWidget

from gyroscope_ui.core.models import CHANNELS
from gyroscope_ui.infrastructure.config import AppConfig

ALWAYS_SHOWN = ("frequency_hz", "gyro_z_rad_s")
_PLOT_OF = {
    "frequency_hz": "frequency",
    "gyro_x_rad_s": "gyro",
    "gyro_y_rad_s": "gyro",
    "gyro_z_rad_s": "gyro",
    "accel_x_m_s2": "accel",
    "accel_y_m_s2": "accel",
    "accel_z_m_s2": "accel",
}
_Y_AXIS_WIDTH = 64  # px; equal widths keep the stacked time axes aligned
# Fixed hues instead of the palette's highlight colour, which is a dark blue that is hard to
# see on a dark background (especially in an inactive window on macOS).
_HUES = {"frequency": 28, "x": 0, "y": 125, "z": 212}
_PEN_WIDTH = 1.5
_LEGEND_ALPHA = 200
_CURSOR_ALPHA = 170
_MARKER_SIZE = 9  # px
_READOUT_OFFSET = (8, 4)  # px from the top left corner of the plot area
_READOUT_ALPHA = 215
_MIN_PLOT_HEIGHT = 70  # px
_UNIT = re.compile(r"\(([^()]*)\)\s*$")  # "Rotationsfrequenz (Hz)" -> "Hz"
# The dividers between the plots: a slim bar in the middle that lights up under the mouse.
_SPLITTER_STYLE = """
QSplitter::handle:vertical { background: transparent; height: 7px; }
QSplitter::handle:vertical:hover { background: palette(highlight); }
"""


class _PlotView(pg.PlotWidget):
    """A plot in its own view; reports when the mouse leaves it."""

    cursor_left = Signal()

    def leaveEvent(self, event: QEvent) -> None:  # noqa: N802
        super().leaveEvent(event)
        self.cursor_left.emit()


class GyroPlot(QSplitter):
    """Stacked, x-linked plots of the measured channels; used as a promoted widget."""

    _ready = False  # class attribute: Qt sends change events while the base class initialises

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(Qt.Orientation.Vertical, parent)
        self.setChildrenCollapsible(False)
        self.setHandleWidth(7)
        self.setStyleSheet(_SPLITTER_STYLE)
        self._all_channels = False
        self._auto_scroll = False
        self._window_s = 60.0
        self._cursor_x: float | None = None
        self._last: tuple[np.ndarray, Mapping[str, np.ndarray]] | None = None
        self._texts: dict[str, str] = {}
        self._legend_names: dict[str, str] = {}
        self._x_label = ""

        self._views: dict[str, _PlotView] = {}
        self._plots: dict[str, pg.PlotItem] = {}
        for key in ("frequency", "gyro", "accel"):
            view = _PlotView()
            view.setAntialiasing(False)
            view.setMinimumHeight(_MIN_PLOT_HEIGHT)
            view.scene().sigMouseMoved.connect(lambda pos, key=key: self._on_mouse_moved(key, pos))
            view.cursor_left.connect(self._on_cursor_left)
            self.addWidget(view)
            self._views[key] = view
            self._plots[key] = view.getPlotItem()
        self.frequency_plot: pg.PlotItem = self._plots["frequency"]
        self.gyro_plot: pg.PlotItem = self._plots["gyro"]
        self.accel_plot: pg.PlotItem = self._plots["accel"]  # visible only with all channels
        self._views["accel"].setVisible(False)
        for plot in self._plots.values():
            plot.showGrid(x=True, y=True, alpha=0.3)
            # The plot hands these to every curve added to it.
            plot.setDownsampling(auto=True, mode="peak")
            plot.setClipToView(True)
            plot.getViewBox().setAutoVisible(y=True)
            plot.getAxis("left").setWidth(_Y_AXIS_WIDTH)
            for axis in ("left", "bottom"):
                plot.getAxis(axis).enableAutoSIPrefix(False)
        self.gyro_plot.setXLink(self.frequency_plot)
        self.accel_plot.setXLink(self.frequency_plot)
        self._legends = {
            "gyro": self.gyro_plot.addLegend(offset=(-10, 10)),
            "accel": self.accel_plot.addLegend(offset=(-10, 10)),
        }

        self._curves: dict[str, pg.PlotDataItem] = {}
        self._markers: dict[str, pg.ScatterPlotItem] = {}
        for name in CHANNELS:
            curve = pg.PlotDataItem(connect="finite")
            curve.setVisible(name in ALWAYS_SHOWN)
            self._plots[_PLOT_OF[name]].addItem(curve)
            self._curves[name] = curve
            marker = pg.ScatterPlotItem(pxMode=True, size=_MARKER_SIZE)
            marker.setZValue(10)
            self._plots[_PLOT_OF[name]].addItem(marker, ignoreBounds=True)
            self._markers[name] = marker

        self._vlines: dict[str, pg.InfiniteLine] = {}
        self._readouts: dict[str, pg.TextItem] = {}
        for key, plot in self._plots.items():
            self._vlines[key] = pg.InfiniteLine(angle=90, movable=False)
            self._readouts[key] = pg.TextItem(anchor=(0, 0))
            self._readouts[key].setZValue(20)
            # ``ignoreBounds``: the cursor must not take part in auto-ranging.
            plot.addItem(self._vlines[key], ignoreBounds=True)
            self._readouts[key].setParentItem(plot.getViewBox())
            self._readouts[key].setPos(*_READOUT_OFFSET)
        self._hide_cursor()

        self._ready = True
        self._apply_palette()
        self.set_all_channels(False)

    # ---- texts and colours ---------------------------------------------------------------
    def apply_config(self, config: AppConfig) -> None:
        """Titles, axis labels and legend names (``ui.gyro_plot``)."""
        for key in (
            "title_frequency",
            "title_gyro",
            "title_accel",
            "label_frequency",
            "label_gyro",
            "label_accel",
        ):
            self._texts[key] = config.text(f"gyro_plot.{key}")
        self._legend_names = {
            name: config.text(f"gyro_plot.legend.{name}")
            for name in CHANNELS
            if name != "frequency_hz"
        }
        self._x_label = config.text("gyro_plot.label_time")
        self._apply_palette()

    def set_x_label(self, text: str) -> None:
        """Label of the time axis (shown under the lowest visible plot)."""
        self._x_label = text
        self._apply_texts()

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        super().changeEvent(event)
        if self._ready and event.type() in (
            QEvent.Type.PaletteChange,
            QEvent.Type.ApplicationPaletteChange,
        ):
            self._apply_palette()

    def _channel_color(self, name: str) -> QColor:
        hue = _HUES["frequency" if name == "frequency_hz" else name.split("_")[1]]
        dark = self.palette().base().color().lightness() < 128
        return QColor.fromHsv(hue, 160, 255) if dark else QColor.fromHsv(hue, 230, 190)

    def _apply_palette(self) -> None:
        palette = self.palette()
        text = palette.text().color()
        base = palette.base().color()
        for view in self._views.values():
            view.setBackground(base)
        for plot in self._plots.values():
            for axis in ("left", "bottom"):
                item = plot.getAxis(axis)
                item.setPen(pg.mkPen(text))
                item.setTextPen(pg.mkPen(text))
        for name, curve in self._curves.items():
            curve.setPen(pg.mkPen(self._channel_color(name), width=_PEN_WIDTH))
        cursor = QColor(text)
        cursor.setAlpha(_CURSOR_ALPHA)
        for line in self._vlines.values():
            line.setPen(pg.mkPen(cursor, width=1, style=Qt.PenStyle.DashLine))
        readout_fill = QColor(base)
        readout_fill.setAlpha(_READOUT_ALPHA)
        for readout in self._readouts.values():
            readout.setColor(text)
            readout.fill = pg.mkBrush(readout_fill)
            readout.border = pg.mkPen(palette.mid().color())
        legend_brush = QColor(base)
        legend_brush.setAlpha(_LEGEND_ALPHA)
        for legend in self._legends.values():
            legend.setLabelTextColor(text)
            legend.setBrush(legend_brush)
            legend.setPen(pg.mkPen(palette.mid().color()))
        self._apply_texts()
        self._rebuild_legends()
        self._update_cursor()

    def _visible_plots(self) -> list[str]:
        return ["frequency", "gyro", *(["accel"] if self._all_channels else [])]

    def _apply_texts(self) -> None:
        color = self.palette().text().color().name()
        for key, plot in self._plots.items():
            plot.setTitle(self._texts.get(f"title_{key}", ""), color=color)
            plot.setLabel("left", self._texts.get(f"label_{key}", ""), color=color)
        last = self._visible_plots()[-1]
        for key, plot in self._plots.items():
            axis = plot.getAxis("bottom")
            axis.showLabel(key == last)
            if key == last:
                plot.setLabel("bottom", self._x_label, color=color)

    def _rebuild_legends(self) -> None:
        for key, legend in self._legends.items():
            legend.clear()
            for name, curve in self._curves.items():
                if _PLOT_OF[name] == key and curve.isVisible():
                    legend.addItem(curve, self._legend_names.get(name, name))

    # ---- cursor --------------------------------------------------------------------------
    def _on_mouse_moved(self, key: str, scene_pos: QPointF) -> None:
        """The mouse moved over the view of plot ``key``: follow it with the cursor."""
        view_box = self._plots[key].getViewBox()
        if key not in self._visible_plots() or not view_box.sceneBoundingRect().contains(scene_pos):
            self._on_cursor_left()  # over an axis or the title: no cursor
            return
        self._cursor_x = float(view_box.mapSceneToView(scene_pos).x())
        self._update_cursor()

    def _on_cursor_left(self) -> None:
        self._cursor_x = None
        self._hide_cursor()

    def _hide_cursor(self) -> None:
        for key in self._plots:
            self._vlines[key].setVisible(False)
            self._readouts[key].setVisible(False)
        for marker in self._markers.values():
            marker.setVisible(False)

    def _nearest_sample(self, x: float) -> int | None:
        """Index of the stored sample nearest to ``x``; ``None`` outside the data."""
        if self._last is None or len(self._last[0]) == 0:
            return None
        t = self._last[0]
        if not (t[0] <= x <= t[-1]):  # also False for NaN
            return None
        i = int(np.searchsorted(t, x))
        if i > 0 and (i == len(t) or x - t[i - 1] <= t[i] - x):
            i -= 1
        return i

    def _update_cursor(self) -> None:
        """Place the cursor at ``_cursor_x`` (snapped to the nearest sample if there is one) and
        refresh the markers and read-outs; hidden while the mouse is not over a plot."""
        if self._cursor_x is None:
            return
        index = self._nearest_sample(self._cursor_x)
        x = self._cursor_x if index is None or self._last is None else float(self._last[0][index])
        visible = self._visible_plots()
        text = self.palette().text().color().name()
        for key in self._plots:
            shown = key in visible
            self._vlines[key].setVisible(shown)
            self._readouts[key].setVisible(shown)
            if shown:
                self._vlines[key].setPos(x)
                lines = [f'<span style="color:{text}">t = {x:.2f} s</span>']
                if index is not None:
                    lines += self._values_at(key, index)
                self._readouts[key].setHtml("<br>".join(lines))
        halo = pg.mkPen(self.palette().base().color(), width=1.5)
        for name, marker in self._markers.items():
            y = self._value(name, index)
            show = y is not None and self._curves[name].isVisible()
            marker.setVisible(show)
            if show:
                brush = pg.mkBrush(self._channel_color(name))
                marker.setData([x], [y], brush=brush, pen=halo, size=_MARKER_SIZE)

    def _value(self, name: str, index: int | None) -> float | None:
        """Finite value of channel ``name`` at sample ``index``, else ``None``."""
        if index is None or self._last is None:
            return None
        column = self._last[1].get(name)
        if column is None or index >= len(column) or not np.isfinite(column[index]):
            return None
        return float(column[index])

    def _values_at(self, key: str, index: int) -> list[str]:
        """Read-out lines of the visible curves of plot ``key`` at sample ``index``."""
        unit_match = _UNIT.search(self._texts.get(f"label_{key}", ""))
        unit = f" {unit_match.group(1)}" if unit_match else ""
        lines = []
        for name, curve in self._curves.items():
            if _PLOT_OF[name] != key or not curve.isVisible():
                continue
            value = self._value(name, index)
            shown = "–" if value is None else f"{value:.4g}{unit}"
            label = self._legend_names.get(name)
            color = self._channel_color(name).name()
            prefix = f"{label} = " if label else ""
            lines.append(f'<span style="color:{color}">{prefix}{shown}</span>')
        return lines

    # ---- data ----------------------------------------------------------------------------
    @property
    def curves(self) -> Mapping[str, pg.PlotDataItem]:
        """The curve of every channel (hidden ones are not drawn)."""
        return self._curves

    @property
    def views(self) -> Mapping[str, pg.PlotWidget]:
        """The view of each plot (``frequency``, ``gyro``, ``accel``)."""
        return self._views

    @property
    def all_channels(self) -> bool:
        return self._all_channels

    def set_data(self, t_s: np.ndarray, columns: Mapping[str, np.ndarray]) -> None:
        """Show the time axis ``t_s`` and the channels in ``columns`` (keys from
        ``core.models.CHANNELS``). Channels that are not shown (all-channels off) are ignored,
        missing ones are cleared."""
        t = np.asarray(t_s, dtype=np.float64)
        self._last = (t, columns)
        if self._auto_scroll:
            self._follow(t)
        for name, curve in self._curves.items():
            if not curve.isVisible():
                continue
            y = columns.get(name)
            if y is None or len(t) == 0:
                curve.setData([], [])
                continue
            y = np.asarray(y, dtype=np.float64)
            if len(y) != len(t):
                raise ValueError(f"{name}: {len(y)} values for {len(t)} time stamps")
            curve.setData(t, y)
        self._update_cursor()  # the data moved under a resting mouse

    def clear(self) -> None:
        """Remove all data and show an empty view."""
        self._last = None
        for curve in self._curves.values():
            curve.setData([], [])
        if self._auto_scroll:
            self.frequency_plot.setXRange(0.0, self._window_s, padding=0)
        else:
            self.auto_range()
        self._update_cursor()

    # ---- view ----------------------------------------------------------------------------
    def set_all_channels(self, on: bool) -> None:
        """Show (or hide) the acceleration plot and the x / y angular rates."""
        changed = on != self._all_channels
        self._all_channels = on
        for name, curve in self._curves.items():
            curve.setVisible(on or name in ALWAYS_SHOWN)
            if not curve.isVisible():
                curve.setData([], [])
        self._views["accel"].setVisible(on)
        if changed:  # start from equal heights again
            visible = self._visible_plots()
            height = max(self.height(), len(visible) * _MIN_PLOT_HEIGHT)
            self.setSizes([height // len(visible) if key in visible else 0 for key in self._plots])
        self._apply_texts()
        self._rebuild_legends()
        if self._last is not None:
            self.set_data(*self._last)
        else:
            self._update_cursor()

    def set_auto_scroll(self, enabled: bool, window_s: float) -> None:
        """With ``enabled`` the x range follows the newest time stamp: ``[t_max - window_s,
        t_max]`` once the data are longer than the window (see :meth:`_follow`). Disabling
        keeps the current range and makes the time axis zoomable again."""
        self._auto_scroll = enabled
        self._window_s = max(float(window_s), 1e-3)
        for plot in self._plots.values():
            plot.setMouseEnabled(x=not enabled, y=True)
        if enabled:
            for plot in self._plots.values():
                plot.getViewBox().disableAutoRange(axis=pg.ViewBox.XAxis)
            if self._last is not None:
                self._follow(self._last[0])

    def auto_range(self) -> None:
        """Re-enable automatic ranging (y always, the time axis unless auto-scroll follows it)."""
        for plot in self._plots.values():
            plot.getViewBox().enableAutoRange(axis=pg.ViewBox.YAxis)
        if not self._auto_scroll:
            self.frequency_plot.getViewBox().enableAutoRange(axis=pg.ViewBox.XAxis)

    def x_range(self) -> tuple[float, float]:
        """The visible time range."""
        left, right = self.frequency_plot.getViewBox().viewRange()[0]
        return float(left), float(right)

    def _follow(self, t: np.ndarray) -> None:
        """Show the newest ``window_s`` seconds. While the data are shorter than the window,
        a recording (t from 0) fills it from the left and the preview (t up to 0 = now) shows
        exactly its data, so no empty stretch appears before the first sample."""
        finite = t[np.isfinite(t)] if len(t) else t
        if len(finite) == 0:
            return
        t_min, t_max = float(finite.min()), float(finite.max())
        if t_max - t_min >= self._window_s:
            left, right = t_max - self._window_s, t_max
        elif t_max <= 0.0:
            left, right = t_min, max(t_max, t_min + 1e-3)
        else:
            left, right = t_min, t_min + self._window_s
        self.frequency_plot.setXRange(left, right, padding=0)
