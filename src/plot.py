from typing import Tuple, Optional
import numpy as np
import matplotlib
try:  # pragma: no cover - optional Qt backend for headless tests
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    matplotlib.use("Qt5Agg")
except Exception:  # If no Qt backend is available fall back to Agg
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvasQTAgg
    matplotlib.use("Agg")

from matplotlib.figure import Figure
from src.debug_utils import Debug


class PlotWidget(FigureCanvasQTAgg):
    """
    A matplotlib-based plot widget for displaying data in real-time.
    Optimized for efficient updates and memory usage.
    """

    def __init__(
        self,
        max_plot_points: int = 100,
        width: int = 5,
        height: int = 4,
        dpi: int = 100,
        fontsize: int = 10,
        xlabel: str = "X",
        ylabel: str = "Y",
        title: str = "Data",
    ):
        """
        Initialize the plot widget with the given parameters.

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
        # Debugging für Plot-Initialisierung
        try:
            Debug.info(
                f"Initializing PlotWidget with max_points={max_plot_points}, title={title}"
            )

            # Set up the figure and axes for the plot
            self.fig = Figure(figsize=(width / dpi, height / dpi), dpi=dpi)
            self.axes = self.fig.add_subplot(111)

            # Initialize the canvas with transparent background
            super().__init__(self.fig)
            # Setze den Hintergrund des Canvas auf transparent
            self.setStyleSheet("background-color: transparent;")

            # Configure plot settings
            self.max_plot_points = max_plot_points
            self.fontsize = fontsize
            self.axes.tick_params(labelsize=self.fontsize)

            # Initialize data arrays with pre-allocated buffers for efficiency
            self._x_data = np.zeros(max_plot_points)
            self._y_data = np.zeros(max_plot_points)
            self._data_count = 0

            # Set up the plot line with increased visibility
            (self.line,) = self.axes.plot(
                [], [], "w-", linewidth=1.5, marker="o", markersize=3
            )

            # Configure axes labels and appearance
            self.axes.set_xlabel(xlabel, fontsize=fontsize)
            self.axes.set_ylabel(ylabel, fontsize=fontsize)
            self.axes.set_title(title, fontsize=fontsize + 2)
            self.axes.grid(True, alpha=0.3)

            # Make background transparent to match application theme
            self.fig.patch.set_facecolor("none")  # Explizit transparent setzen
            self.axes.patch.set_facecolor("none")  # Explizit transparent setzen
            self.fig.patch.set_alpha(0.0)
            self.axes.patch.set_alpha(0.0)

            # Setze explizit clear=True für FigureCanvasQTAgg, um Transparenz zu ermöglichen
            self.fig.set_facecolor("none")
            self.fig.tight_layout(pad=1.0)

            # Achsen und Text in Weiß für bessere Sichtbarkeit
            for spine in ["top", "bottom", "left", "right"]:
                self.axes.spines[spine].set_color("white")
            self.axes.tick_params(colors="white")
            self.axes.yaxis.label.set_color("white")
            self.axes.xaxis.label.set_color("white")
            self.axes.title.set_color("white")

            # Initial plot appearance
            # self.fig.tight_layout()
            self.axes.autoscale(enable=True, axis="both", tight=True)

            # Store plot configuration
            self._plot_config = {"xlabel": xlabel, "ylabel": ylabel, "title": title}

            Debug.info("PlotWidget initialization complete")
        except Exception as e:
            Debug.error(f"Error initializing PlotWidget: {e}")

    def update_plot(self, new_point: Tuple[float, float]) -> None:
        """
        Add a new data point to the plot and update the display.
        Optimized for efficient updates with large datasets.

        Args:
            new_point (Tuple[float, float]): The new point to add (x, y)
        """
        x, y = new_point

        # Add the new point to our data arrays
        if self._data_count < self.max_plot_points:
            # Still filling the initial buffer
            self._x_data[self._data_count] = x
            self._y_data[self._data_count] = y
            self._data_count += 1
        else:
            # Buffer full, shift data and add new point at the end
            self._x_data = np.roll(self._x_data, -1)
            self._y_data = np.roll(self._y_data, -1)
            self._x_data[-1] = x
            self._y_data[-1] = y

        # Update the line data for display
        self.line.set_data(
            self._x_data[: self._data_count], self._y_data[: self._data_count]
        )

        # Adjust plot limits only when needed for efficiency
        self._adjust_limits()

        # Redraw the canvas
        self.fig.canvas.draw()  # Statt draw_idle() für sofortige Aktualisierung
        self.fig.canvas.flush_events()
        self.update()  # Löst ein explizites QWidget repaint aus

    def _adjust_limits(self) -> None:
        """
        Adjust the plot limits to show all data points with some margin.
        Uses smart rescaling to avoid constant limit changes.
        """
        if self._data_count <= 1:
            # Not enough data for meaningful limits
            self.axes.set_xlim(0, 10)
            self.axes.set_ylim(0, 10)
            return

        # Get current data ranges
        x_min, x_max = np.min(self._x_data[: self._data_count]), np.max(
            self._x_data[: self._data_count]
        )
        y_min, y_max = np.min(self._y_data[: self._data_count]), np.max(
            self._y_data[: self._data_count]
        )

        # Add margin to the limits (5% on each side)
        x_margin = np.float64(max(0.5, (x_max - x_min) * 0.05))
        y_margin = np.float64(max(0.5, (y_max - y_min) * 0.05))

        # Get current view limits
        curr_x_min, curr_x_max = self.axes.get_xlim()
        curr_y_min, curr_y_max = self.axes.get_ylim()

        # Only adjust if data is outside current view or view is much larger than needed
        need_x_update = (
            x_min < curr_x_min + x_margin / 2
            or x_max > curr_x_max - x_margin / 2
            or curr_x_max - curr_x_min > (x_max - x_min + 2 * x_margin) * 1.5
        )

        need_y_update = (
            y_min < curr_y_min + y_margin / 2
            or y_max > curr_y_max - y_margin / 2
            or curr_y_max - curr_y_min > (y_max - y_min + 2 * y_margin) * 1.5
        )

        if need_x_update:
            self.axes.set_xlim(x_min - x_margin, x_max + x_margin)

        if need_y_update:
            self.axes.set_ylim(y_min - y_margin, y_max + y_margin)

    def clear(self) -> None:
        """
        Clear all data points and reset the plot.
        """
        self._data_count = 0
        self.line.set_data([], [])

        # Reset to default limits
        self.axes.set_xlim(0, 10)
        self.axes.set_ylim(0, 10)

        # Redraw the canvas
        self.draw_idle()

    def set_title(self, title: str) -> None:
        """
        Set the title of the plot.

        Args:
            title (str): The new title
        """
        self.axes.set_title(title, fontsize=self.fontsize + 2)
        self._plot_config["title"] = title
        self.draw_idle()

    def set_axis_labels(
        self, xlabel: Optional[str] = None, ylabel: Optional[str] = None
    ) -> None:
        """
        Set the labels for the x and y axes.

        Args:
            xlabel (str, optional): Label for the x-axis
            ylabel (str, optional): Label for the y-axis
        """
        if xlabel is not None:
            self.axes.set_xlabel(xlabel, fontsize=self.fontsize)
            self._plot_config["xlabel"] = xlabel

        if ylabel is not None:
            self.axes.set_ylabel(ylabel, fontsize=self.fontsize)
            self._plot_config["ylabel"] = ylabel

        self.draw_idle()

    def set_max_points(self, max_points: int) -> None:
        """
        Change the maximum number of points to display.

        Args:
            max_points (int): New maximum number of points
        """
        if max_points <= 0:
            return

        self.max_plot_points = max_points

        # Create new data arrays with the new size
        new_x_data = np.zeros(max_points)
        new_y_data = np.zeros(max_points)

        # Copy existing data, truncating if needed
        if self._data_count > 0:
            copy_count = min(self._data_count, max_points)
            start_idx = max(0, self._data_count - max_points)
            new_x_data[:copy_count] = self._x_data[start_idx : start_idx + copy_count]
            new_y_data[:copy_count] = self._y_data[start_idx : start_idx + copy_count]

        # Update data arrays and count
        self._x_data = new_x_data
        self._y_data = new_y_data
        self._data_count = min(self._data_count, max_points)

        # Update the plot
        self.line.set_data(
            self._x_data[: self._data_count], self._y_data[: self._data_count]
        )
        self._adjust_limits()
        self.draw_idle()
