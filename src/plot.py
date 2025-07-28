"""Plot widgets using :mod:`pyqtgraph`."""

from __future__ import annotations

from typing import Iterable, Optional, Tuple, List
import numpy as np

try:  # pragma: no cover - optional dependency during headless tests
    import pyqtgraph as pg
except Exception:  # pragma: no cover - fallback stubs
    from PySide6.QtWidgets import QWidget

    class _DummyPlotWidget(QWidget, object):
        def __init__(self, *_, **__):
            super().__init__()

        def plot(self, *_, **__):
            return self

        def clear(self):
            pass

        def setLabel(self, *_, **__):
            pass

        def setTitle(self, *_):
            pass

        def autoRange(self, *_, **__):
            pass

    pg = type("MockPyQtGraph", (), {"PlotWidget": _DummyPlotWidget})()


class PlotWidget(pg.PlotWidget):
    """A real-time plot widget using pyqtgraph."""

    def __init__(
        self,
        title: Optional[str] = None,
        xlabel: str = "Index",
        ylabel: str = "Time (µs)",
        max_plot_points: int = 500,
        fontsize: int = 12,
    ):
        """
        Initialize the plot widget.

        Args:
            max_plot_points (int): Maximum number of points to display in the plot
            width (int): Width of the plot in inches
            height (int): Height of the plot in inches
            dpi (int): DPI (dots per inch) of the plot
            fontsize (int): Font size to use in the plot
            xlabel (str): Label for the x-axis
            ylabel (str): Label for the y-axis
            title (str): Title of the plot
        """
        super().__init__()

        self.max_plot_points = max_plot_points
        self.fontsize = fontsize
        self._user_interacted = False

        # Set up the plot appearance
        self.setBackground(None)
        self.showGrid(x=True, y=True, alpha=0.3)
        self.setLabel("bottom", xlabel)
        self.setLabel("left", ylabel)
        self.setTitle(title)

        # Store config for potential future use
        self._plot_config = {"xlabel": xlabel, "ylabel": ylabel, "title": title}


        # Redraw the canvas
        self.fig.canvas.draw()  # Use draw() instead of draw_idle() for immediate update
        self.fig.canvas.flush_events()
        self.update()  # Triggers an explicit QWidget repaint

    def _on_view_changed(self):
        """Called when user pans or zooms the plot"""
        self._user_interacted = True

    def update_plot(self, data_points: List[Tuple[int, float, str]]):
        """
        Updates the plot using external data source

        Args:
            data_points: List of (index_num, value_num, timestamp) tuples
        """
        if not data_points:
            return

        # Plot ALL data points for complete history
        all_indices = np.array([point[0] for point in data_points])
        all_values_us = np.array([point[1] for point in data_points])

        # Clear and update plot with ALL data points
        self.clear()
        self._plot_item = self.plot(
            all_indices,
            all_values_us,
            pen="w",  # White connecting line
            symbol="o",
            symbolSize=4,
            symbolBrush="r",
            symbolPen="r",
        )

        # AutoRange calculation based only on LAST max_plot_points for consistent view
        display_data_for_range = (
            data_points[-self.max_plot_points :]
            if len(data_points) > self.max_plot_points
            else data_points
        )

        if len(display_data_for_range) > 0:
            # Extract indices and values for range calculation only
            range_indices = np.array([point[0] for point in display_data_for_range])
            range_values_us = np.array([point[1] for point in display_data_for_range])

            # Calculate proper ranges with minimal padding
            x_min, x_max = range_indices.min(), range_indices.max()
            y_min, y_max = range_values_us.min(), range_values_us.max()

            # Ensure minimum range for single-point plots
            if x_max == x_min:
                x_padding = max(1, x_min * 0.1)  # 10% of index or at least 1
                final_x_range = [x_min - x_padding, x_max + x_padding]
            else:
                x_range = x_max - x_min
                x_padding = x_range * 0.05
                final_x_range = [x_min - x_padding, x_max + x_padding]

            if y_max == y_min:
                y_padding = max(1000, y_min * 0.1)  # 10% of value or at least 1000µs
                final_y_range = [y_min - y_padding, y_max + y_padding]
            else:
                y_range = y_max - y_min
                y_padding = y_range * 0.05
                final_y_range = [y_min - y_padding, y_max + y_padding]

            # Disable automatic autoRange and set manual range
            viewbox = self.plotItem.getViewBox()
            viewbox.enableAutoRange(enable=False)  # Disable PyQtGraph's autoRange
            viewbox.setRange(xRange=final_x_range, yRange=final_y_range, padding=0)

    def get_data_in_range(self, max_points: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Legacy method - no longer needed with centralized data management
        """
        return np.array([]), np.array([])


class HistogramWidget(pg.PlotWidget):
    """A histogram widget using pyqtgraph."""

    def __init__(
        self, title: Optional[str] = None, xlabel: str = "CPM", ylabel: str = "Count"
    ):
        """
        Initialize the histogram widget.

        Args:
            title: Plot title
            xlabel: X-axis label (CPM values)
            ylabel: Y-axis label (frequency count)
        """
        super().__init__()

        self.setBackground(None)
        self.showGrid(x=True, y=True, alpha=0.3)
        self.setLabel("bottom", xlabel)
        self.setLabel("left", ylabel)
        self.setTitle(title)

        self._hist_item = None

    def update_histogram(self, data: Iterable[float], bins: int = 50):
        """
        Update the histogram with new data.

        Args:
            data: CPM values to create histogram from
            bins: Number of histogram bins
        """
        if not data:
            return

        # Calculate histogram
        hist, bin_edges = np.histogram(data, bins=bins)

        # Calculate bin centers and width
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        width = bin_edges[1] - bin_edges[0]

        # Clear previous histogram
        if self._hist_item is not None:
            self.removeItem(self._hist_item)

        # Create new histogram
        self._hist_item = pg.BarGraphItem(
            x=bin_centers,
            height=hist,
            width=width * 0.8,  # Slightly smaller bars
            brush="w",
        )
        self.addItem(self._hist_item)

        # Auto-range to fit data
        self.autoRange()
