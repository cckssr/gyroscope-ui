"""Plots of a measurement (pyqtgraph): rotation frequency over time on top, angular rate below,
and the acceleration as a third plot that exists only with "Alle Kanäle".

The x axes are linked. All curves are created once and updated with ``setData``; nothing loops
over points in Python (downsampling and clipping to the view are pyqtgraph's, ``peak`` mode keeps
spikes visible). Non-finite values leave gaps. Background and text follow the palette, so the plots
follow light and dark mode.

Every plot has a cursor: a crosshair with a read-out of time and value under the mouse; the
vertical line follows the mouse in all visible plots at once.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget

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
_READOUT_OFFSET = (8, 4)  # px from the top left corner of the plot area
_UNIT = re.compile(r"\(([^()]*)\)\s*$")  # "Rotationsfrequenz (Hz)" -> "Hz"


class GyroPlot(pg.GraphicsLayoutWidget):
    """Stacked, x-linked plots of the measured channels; used as a promoted widget."""

    _ready = False  # class attribute: Qt sends change events while the base class initialises

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # pyqtgraph copies ``GraphicsLayout.clear`` onto the instance; ours has to win.
        self.clear = self._clear
        self.setAntialiasing(False)
        self._all_channels = False
        self._auto_scroll = False
        self._window_s = 60.0
        self._last: tuple[np.ndarray, Mapping[str, np.ndarray]] | None = None
        self._texts: dict[str, str] = {}
        self._legend_names: dict[str, str] = {}
        self._x_label = ""

        self.frequency_plot: pg.PlotItem = self.ci.addPlot(row=0, col=0)
        self.gyro_plot: pg.PlotItem = self.ci.addPlot(row=1, col=0)
        self.accel_plot: pg.PlotItem = pg.PlotItem()  # in the layout only with all channels
        self._plots = {
            "frequency": self.frequency_plot,
            "gyro": self.gyro_plot,
            "accel": self.accel_plot,
        }
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

        self._vlines: dict[str, pg.InfiniteLine] = {}
        self._hlines: dict[str, pg.InfiniteLine] = {}
        self._readouts: dict[str, pg.TextItem] = {}
        for key, plot in self._plots.items():
            self._vlines[key] = pg.InfiniteLine(angle=90, movable=False)
            self._hlines[key] = pg.InfiniteLine(angle=0, movable=False)
            self._readouts[key] = pg.TextItem(anchor=(0, 0))
            # ``ignoreBounds``: the cursor must not take part in auto-ranging.
            plot.addItem(self._vlines[key], ignoreBounds=True)
            plot.addItem(self._hlines[key], ignoreBounds=True)
            self._readouts[key].setParentItem(plot.getViewBox())
            self._readouts[key].setPos(*_READOUT_OFFSET)
        self._hide_cursor()
        self.scene().sigMouseMoved.connect(self._on_mouse_moved)

        self._curves: dict[str, pg.PlotDataItem] = {}
        for name in CHANNELS:
            curve = pg.PlotDataItem(connect="finite")
            curve.setVisible(name in ALWAYS_SHOWN)
            self._plots[_PLOT_OF[name]].addItem(curve)
            self._curves[name] = curve

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
        self.setBackground(base)
        for plot in self._plots.values():
            for axis in ("left", "bottom"):
                item = plot.getAxis(axis)
                item.setPen(pg.mkPen(text))
                item.setTextPen(pg.mkPen(text))
        for name, curve in self._curves.items():
            curve.setPen(pg.mkPen(self._channel_color(name), width=_PEN_WIDTH))
        cursor = QColor(text)
        cursor.setAlpha(_CURSOR_ALPHA)
        for line in (*self._vlines.values(), *self._hlines.values()):
            line.setPen(pg.mkPen(cursor, width=1, style=Qt.PenStyle.DashLine))
        for readout in self._readouts.values():
            readout.setColor(text)
            readout.fill = pg.mkBrush(base)
        legend_brush = QColor(base)
        legend_brush.setAlpha(_LEGEND_ALPHA)
        for legend in self._legends.values():
            legend.setLabelTextColor(text)
            legend.setBrush(legend_brush)
            legend.setPen(pg.mkPen(palette.mid().color()))
        self._apply_texts()
        self._rebuild_legends()

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
    def leaveEvent(self, event: QEvent) -> None:  # noqa: N802
        super().leaveEvent(event)
        self._hide_cursor()

    def _hide_cursor(self) -> None:
        for key in self._plots:
            self._vlines[key].setVisible(False)
            self._hlines[key].setVisible(False)
            self._readouts[key].setVisible(False)

    def _on_mouse_moved(self, scene_pos: QPointF) -> None:
        """Move the cursor to the mouse: crosshair and read-out in the plot under the mouse,
        the vertical line alone in the other visible plots."""
        visible = self._visible_plots()
        hovered = next(
            (
                key
                for key in visible
                if self._plots[key].getViewBox().sceneBoundingRect().contains(scene_pos)
            ),
            None,
        )
        if hovered is None:
            self._hide_cursor()
            return
        point = self._plots[hovered].getViewBox().mapSceneToView(scene_pos)
        x, y = float(point.x()), float(point.y())
        for key in self._plots:
            shown = key in visible
            self._vlines[key].setVisible(shown)
            if shown:
                self._vlines[key].setPos(x)
            self._hlines[key].setVisible(key == hovered)
            self._readouts[key].setVisible(key == hovered)
        self._hlines[hovered].setPos(y)
        unit = _UNIT.search(self._texts.get(f"label_{hovered}", ""))
        value = f"{y:.4g}" + (f" {unit.group(1)}" if unit else "")
        self._readouts[hovered].setText(f"t = {x:.2f} s\n{value}")

    # ---- data ----------------------------------------------------------------------------
    @property
    def curves(self) -> Mapping[str, pg.PlotDataItem]:
        """The curve of every channel (hidden ones are not drawn)."""
        return self._curves

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

    def clear(self) -> None:
        """Remove all data and show an empty view."""
        self._clear()

    def _clear(self) -> None:
        self._last = None
        for curve in self._curves.values():
            curve.setData([], [])
        if self._auto_scroll:
            self.frequency_plot.setXRange(0.0, self._window_s, padding=0)
        else:
            self.auto_range()

    # ---- view ----------------------------------------------------------------------------
    def set_all_channels(self, on: bool) -> None:
        """Show (or hide) the acceleration plot and the x / y angular rates."""
        self._all_channels = on
        for name, curve in self._curves.items():
            curve.setVisible(on or name in ALWAYS_SHOWN)
            if not curve.isVisible():
                curve.setData([], [])
        accel_in_layout = self.accel_plot in self.ci.items
        if on and not accel_in_layout:
            self.ci.addItem(self.accel_plot, row=2, col=0)
        elif not on and accel_in_layout:
            self.ci.removeItem(self.accel_plot)
        self.accel_plot.setVisible(on)
        self._apply_texts()
        self._rebuild_legends()
        if self._last is not None:
            self.set_data(*self._last)

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
