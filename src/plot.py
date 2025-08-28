"""Plot widgets using :mod:`pyqtgraph`."""

from __future__ import annotations

from typing import Iterable, Optional, Tuple, List
from collections import deque
import queue
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Slot  # pylint: disable=no-name-in-module

from src.debug_utils import Debug


class PlotWidget(pg.GraphicsLayoutWidget):
    """A real-time plot widget using pyqtgraph."""

    def __init__(
        self,
        series_cfg: List[dict[str, str | int]],
        max_plot_points: int = 500,
        fontsize: int = 12,
    ):
        """
        Initialize the plot widget.

        Args:
            series_cfg (List[dict[str, str | int]]): Configuration for the series to plot
                - 'name': str Defining the name of the plot
                - 'y_index': int Index of the Signal for the y-axis
                - 'title': str | int Title of the plot
            max_plot_points (int): Maximum number of points to display in the plot
            fontsize (int): Font size to use in the plot
        """
        super().__init__()

        self.fontsize = fontsize
        self.max_points = max_plot_points
        # Setup data buffers with common x-axis
        self.x_data = deque(maxlen=max_plot_points)
        self.series = {}
        self._user_interacted = False

        # Auto-scrolling control
        self.auto_scroll_enabled = True

        # Measurement markers
        self.measurement_markers = []  # List of vertical line items
        self.plots = []  # Store plot items for adding markers

        # Queue for incoming data points
        self.data_queue = queue.Queue()

        # Create plots for each series
        self._setup_plots(series_cfg)

    def _setup_plots(self, series):
        top_plot = None
        for i, cfg in enumerate(series):
            p = self.addPlot(
                row=i, col=0, title=cfg.get("title", cfg.get("name", "Plot"))
            )
            p.showGrid(x=True, y=True, alpha=0.3)

            # Store plot reference for markers
            self.plots.append(p)

            if top_plot is None:
                top_plot = p
            else:
                p.setXLink(top_plot)
            curve = p.plot(
                [],
                [],
                pen="w",  # White connecting line
                symbol="o",
                symbolSize=4,
                symbolBrush="r",
                symbolPen="r",
            )
            self.series[cfg["name"]] = {
                "curve": curve,
                "y": deque(maxlen=self.max_points),
                "y_index": cfg["y_index"],
                "plot": p,  # Store plot reference in series
            }

    def autoRange(self):
        """Automatically adjust the view range to fit all data."""
        for s in self.series.values():
            s["curve"].setAutoVisible(y=True)

    # The data is emitted with the multi_data_signal
    @Slot(float, float, float, float)
    def on_new_point(self, elapsed_sec, freq, accel_z, gyro_z):
        """Add a new data point to the queue for later processing."""
        try:
            # Put data in queue for batch processing
            self.data_queue.put_nowait((elapsed_sec, freq, accel_z, gyro_z))
        except queue.Full:
            # Queue is full, skip this point (shouldn't happen with unlimited queue)
            pass

    def update_plots(self):
        """Process queued data points and update plots. Called by external timer."""
        if self.data_queue.empty():
            return

        # Process all queued data points
        points_processed = 0
        while (
            not self.data_queue.empty() and points_processed < 100
        ):  # Limit to avoid blocking
            try:
                elapsed_sec, freq, accel_z, gyro_z = self.data_queue.get_nowait()
                self._add_data_point(elapsed_sec, freq, accel_z, gyro_z)
                points_processed += 1
            except queue.Empty:
                break

        # Update all plot curves with new data
        self._refresh_curves()

    def _add_data_point(self, elapsed_sec, freq, accel_z, gyro_z):
        """Add a single data point to the internal buffers."""
        vals = (elapsed_sec, freq, accel_z, gyro_z)
        self.x_data.append(elapsed_sec)

        # Update each series buffer
        for name, s in self.series.items():
            y = float(vals[s["y_index"]])
            if not np.isfinite(y):
                y = np.nan
            s["y"].append(y)

    def _refresh_curves(self):
        """Update all plot curves with current data."""
        if not self.x_data:
            return

        x_arr = np.array(self.x_data, dtype=float)
        for name, s in self.series.items():
            if s["y"]:
                y_arr = np.array(s["y"], dtype=float)
                s["curve"].setData(x_arr, y_arr)

                # Auto-scroll to latest data if enabled
                if self.auto_scroll_enabled and len(x_arr) > 0:
                    plot = s["plot"]
                    plot.setXRange(x_arr[0], x_arr[-1], padding=0.02)

    def add_measurement_marker(self, x_position: float, is_start: bool = True):
        """Add a vertical line marker to indicate measurement start/stop.

        Args:
            x_position: X-coordinate (time) where to place the marker
            is_start: True for start marker (green), False for stop marker (red)
        """
        color = "g" if is_start else "r"
        marker_type = "START" if is_start else "STOP"

        # Add marker to all plots
        for plot in self.plots:
            line = pg.InfiniteLine(
                pos=x_position, angle=90, pen=pg.mkPen(color, width=2)
            )
            line.setToolTip(f"Measurement {marker_type} at {x_position:.2f}s")
            plot.addItem(line)
            self.measurement_markers.append(line)

    def set_auto_scroll(self, enabled: bool):
        """Enable or disable auto-scrolling to latest data.

        Args:
            enabled: True to enable auto-scrolling, False to disable
        """
        self.auto_scroll_enabled = enabled
        if enabled:
            # If re-enabling, scroll to latest data immediately
            self._refresh_curves()

    def clear_measurement_markers(self):
        """Remove all measurement markers from the plots."""
        for marker in self.measurement_markers:
            for plot in self.plots:
                try:
                    plot.removeItem(marker)
                except:
                    pass  # Marker might already be removed
        self.measurement_markers.clear()

    def get_queue_size(self) -> int:
        """Get the current size of the data queue.

        Returns:
            Current number of items in queue
        """
        try:
            return self.data_queue.qsize()
        except AttributeError:
            return 0


class HistogramWidget(pg.PlotWidget):  # type: ignore
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
        # Ensure sequence
        try:
            data_seq = list(data)
        except TypeError:
            return
        if not data_seq:
            return
        hist, bin_edges = np.histogram(np.asarray(data_seq, dtype=float), bins=bins)

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
