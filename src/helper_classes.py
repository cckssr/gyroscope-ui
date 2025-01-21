import matplotlib
import re
from PySide6.QtWidgets import QStatusBar, QLabel, QMessageBox
from PySide6.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
matplotlib.use('Qt5Agg')

class MplCanvas(FigureCanvasQTAgg):
    """
    A custom Matplotlib canvas for embedding plots in a PyQt application.
    Attributes:
        axes (matplotlib.axes.Axes): The main axes of the figure.
    Methods:
        __init__(width=5, height=4, dpi=100):
            Initializes the canvas with a figure of specified width, height, and dpi.
        _configure_axes(fontsize: int = 10, xlabel: str = 'x', ylabel: str = 'y'):
            Configures the appearance of the axes, including tick parameters, labels, and colors.
    """

    def __init__(self, width=5, height=4, dpi=100, 
                 fontsize: int = 10, xlabel: str = 'x', ylabel: str = 'y'):
        """
        Initializes a new instance of the class.
        Parameters:
            width (int): The width of the figure in inches. Default is 5.
            height (int): The height of the figure in inches. Default is 4.
            dpi (int): The resolution of the figure in dots per inch. Default is 100.
            fontsize (int): The font size for the axis labels and tick labels. Default is 10.
            xlabel (str): The label for the x-axis. Default is 'x'.
            ylabel (str): The label for the y-axis. Default is 'y'.
        """
        self.fontsize = fontsize
        self.xlabel = xlabel
        self.ylabel = ylabel
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1)
        fig.patch.set_facecolor('none')
        fig.patch.set_edgecolor('none')
        self.axes = fig.add_subplot(111)
        self._configure_axes()
        super().__init__(fig)

    def _configure_axes(self):
        """
        Configures the appearance of the axes in the plot.
        This method sets the font size and color for the x and y axis labels, 
        sets the face color of the axes to transparent, and changes the color 
        of the tick labels and the axes spines to white.
        """
        self.axes.tick_params(labelsize=self.fontsize)
        self.axes.set_xlabel(self.xlabel, fontsize=self.fontsize, color='white')
        self.axes.set_ylabel(self.ylabel, fontsize=self.fontsize, color='white')
        self.axes.set_facecolor('none')
        self.axes.tick_params(colors='white')
        # set axes color to white
        for spine in self.axes.spines.values():
            spine.set_color('white')

class PlotWidget(MplCanvas):
    """
    A widget for plotting data using Matplotlib.

    Attributes:
        _max_points (int): The maximum number of points to display on the plot.
        _parent: The parent widget.
        _plot_ref: A reference to the plot line.
        xdata (list): The x-axis data points.
        ydata (list): The y-axis data points.

    Methods:
        __init__(parent=None, max_plot_points: int = 50, **kwargs):
            Initializes the PlotWidget with optional parent and maximum plot points.
        
        _setup_plot():
            Sets up the initial plot with the initial x and y data.
        
        update_plot(new_ydata, new_xdata=None):
            Updates the plot with new y data and optionally new x data.
    """
    def __init__(self, parent=None, max_plot_points: int = 50, **kwargs):
        super().__init__(**kwargs)
        self._max_points = max_plot_points
        self._parent = parent
        self._plot_ref = None
        self.xdata = [0]
        self.ydata = [0]
        self._setup_plot()

    def _setup_plot(self):
        self._plot_ref = self.axes.plot(self.xdata, self.ydata)

    def update_plot(self, new_ydata, new_xdata=None):
        self.ydata = self.ydata[-self._max_points:] + [new_ydata]
        # if new x data is provided, use it, otherwise increment the last x data by 1
        if new_xdata:
            self.xdata = self.xdata[-self._max_points:] + [new_xdata]
        else:
            self.xdata = self.xdata[-self._max_points:] + [self.xdata[-1] + 1]

        # self.ydata = self.ydata[-self._max_points:] + [random.randint(100, 500)]
        self._plot_ref[0].set_data(self.xdata, self.ydata)
        self._plot_ref[0].axes.relim()
        self._plot_ref[0].axes.autoscale_view()
        self.draw()

class Statusbar():
    def __init__(self, statusbar: QStatusBar):
        self.statusbar = statusbar
        self.old_state = None
        self._save_state()

    def temp_message(self, message: str, backcolor: str = None, duration: int = None):
        new_style = self._update_statusbar_style(backcolor)
        # set statusbar style
        self.statusbar.setStyleSheet(new_style)

        # Set new message and if duration is provided, reset after the duration elapses
        if duration:
            self.statusbar.showMessage(message, duration)
            # reset to old state after duration
            QTimer.singleShot(duration, lambda: self.statusbar.setStyleSheet(self.old_state[1]))
            QTimer.singleShot(duration, lambda: self.statusbar.showMessage(self.old_state[0]))
        else:
            self.statusbar.showMessage(message)

    def perm_message(self, message: str, index: int = 0, backcolor: str = None):
        new_style = self._update_statusbar_style(backcolor)
        self.statusbar.setStyleSheet(new_style)
        label = QLabel()
        label.setText(message)
        self.statusbar.insertPermanentWidget(index, label)

    def _update_statusbar_style(self, backcolor):
        # get current state
        self._save_state()

        # Set new style if backcolor is provided or keep the old style
        if backcolor:
            if "background-color:" in self.old_state[1]:
                # if old style had backcolor, replace it with the new one
                new_style = self.old_state[1].replace(
                    re.search(r"background-color:\s*[^;]+;", self.old_state[1]).group(0),
                    f"background-color: {backcolor};"
                )
            else:
                # otherwise append the new backcolor
                new_style = self.old_state[1] + f"background-color: {backcolor};"
        else:
            new_style = self.old_state[1]
        return new_style

    def _save_state(self):
        self.old_state = [self.statusbar.currentMessage(), self.statusbar.styleSheet()]

class Helper():
    @staticmethod
    def close_event(parent, event):
        reply = QMessageBox.question(parent,
                    'Beenden',
                    'Wollen Sie sicher das Programm schließen?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
