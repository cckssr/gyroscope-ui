"""Plot widgets using :mod:`pyqtgraph`."""

from __future__ import annotations

from typing import Iterable, Optional, Tuple
import numpy as np

try:  # pragma: no cover - optional dependency during headless tests
    import pyqtgraph as pg
except Exception:  # pragma: no cover - fallback stubs
    from PySide6.QtWidgets import QWidget

    class _DummyPlotWidget(QWidget):
        def __init__(self, *_, **__):
            super().__init__()

        def plot(self, *_, **__):
            return self

        def setData(self, *_, **__):
            pass

        def clear(self):
            pass

        def addItem(self, *_):
            pass

        def autoRange(self, *_, **__):
            pass

        def setBackground(self, *_):
            pass

        def showGrid(self, *_, **__):
            pass

        def setLabel(self, *_, **__):
            pass

        def setTitle(self, *_, **__):
            pass

    pg = type("pg", (), {"PlotWidget": _DummyPlotWidget, "mkPen": lambda *a, **k: None, "BarGraphItem": object})()  # type: ignore

from src.debug_utils import Debug


class PlotWidget(pg.PlotWidget):
    """Real-time line plot widget."""

    def __init__(
        self,
        max_plot_points: int = 100,
        width: int | None = None,
        height: int | None = None,
        dpi: int | None = None,
        fontsize: int = 10,
        xlabel: str = "X",
        ylabel: str = "Y",
        title: str = "Data",
    ) -> None:
        super().__init__()

        Debug.info(
            f"Initializing PlotWidget with max_points={max_plot_points}, title={title}"
        )

        self.setBackground(None)
        self.showGrid(x=True, y=True, alpha=0.3)

        self.max_plot_points = max_plot_points
        self.fontsize = fontsize

        self._x_data = np.zeros(max_plot_points)
        self._y_data = np.zeros(max_plot_points)
        self._data_count = 0

        pen = pg.mkPen("w", width=1.5)
        self.line = self.plot([], [], pen=pen, symbol="o", symbolSize=3)

        self.setLabel("bottom", xlabel)
        self.setLabel("left", ylabel)
        self.setTitle(title)

        self._plot_config = {"xlabel": xlabel, "ylabel": ylabel, "title": title}

    # ------------------------------------------------------------------
    def update_plot(self, new_point: Tuple[float, float]) -> None:
        """Add a new point to the line plot."""

        x, y = new_point

        if self._data_count < self.max_plot_points:
            self._x_data[self._data_count] = x
            self._y_data[self._data_count] = y
            self._data_count += 1
        else:
            self._x_data = np.roll(self._x_data, -1)
            self._y_data = np.roll(self._y_data, -1)
            self._x_data[-1] = x
            self._y_data[-1] = y

        self.line.setData(
            self._x_data[: self._data_count], self._y_data[: self._data_count]
        )
        self.autoRange()

    # ------------------------------------------------------------------
    def clear(self) -> None:  # type: ignore[override]
        """Clear the plot data."""

        self._data_count = 0
        self._x_data[:] = 0
        self._y_data[:] = 0
        self.line.setData([], [])
        super().clear()

    # ------------------------------------------------------------------
    def set_title(self, title: str) -> None:
        self.setTitle(title)
        self._plot_config["title"] = title

    # ------------------------------------------------------------------
    def set_axis_labels(
        self, xlabel: Optional[str] = None, ylabel: Optional[str] = None
    ) -> None:
        if xlabel is not None:
            self.setLabel("bottom", xlabel)
            self._plot_config["xlabel"] = xlabel
        if ylabel is not None:
            self.setLabel("left", ylabel)
            self._plot_config["ylabel"] = ylabel

    # ------------------------------------------------------------------
    def set_max_points(self, max_points: int) -> None:
        if max_points <= 0:
            return

        new_x = np.zeros(max_points)
        new_y = np.zeros(max_points)

        copy_count = min(self._data_count, max_points)
        if copy_count > 0:
            start_idx = max(0, self._data_count - max_points)
            new_x[:copy_count] = self._x_data[start_idx : start_idx + copy_count]
            new_y[:copy_count] = self._y_data[start_idx : start_idx + copy_count]

        self._x_data = new_x
        self._y_data = new_y
        self._data_count = copy_count
        self.max_plot_points = max_points

        self.line.setData(
            self._x_data[: self._data_count], self._y_data[: self._data_count]
        )
        self.autoRange()


class HistogramWidget(pg.PlotWidget):
    """Widget for displaying histograms."""

    def __init__(
        self,
        bins: int = 50,
        fontsize: int = 10,
        xlabel: str = "Value",
        ylabel: str = "Count",
        title: str = "Histogram",
    ) -> None:
        super().__init__()

        self.setBackground(None)
        self.showGrid(x=True, y=True, alpha=0.3)

        self.bins = bins
        self.fontsize = fontsize

        self.setLabel("bottom", xlabel)
        self.setLabel("left", ylabel)
        self.setTitle(title)

        self._hist_item: Optional[pg.BarGraphItem] = None

    # ------------------------------------------------------------------
    def update_histogram(self, values: Iterable[float]) -> None:
        """Update histogram with new values."""

        vals = list(values)
        if not vals:
            self.clear()
            return

        hist, edges = np.histogram(vals, bins=self.bins)
        width = edges[1] - edges[0]
        x = edges[:-1] + width / 2.0

        self.clear()
        self._hist_item = pg.BarGraphItem(x=x, height=hist, width=width, brush="w")
        self.addItem(self._hist_item)
        self.autoRange()

    # ------------------------------------------------------------------
    def set_bins(self, bins: int) -> None:
        if bins > 0:
            self.bins = bins
