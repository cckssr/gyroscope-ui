import sys
import random
import matplotlib

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PySide6.QtCore import Slot, QTimer
#from PySide6.QtGui import QIcon
from serial.tools import list_ports
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_MainWindow

matplotlib.use('Qt5Agg')


# Greetings
@Slot()
def say_hello():
    print("Button clicked, Hello!")

def get_comports():
    return [[port.device, port.description] for port in list_ports.comports()]

class MplCanvas(FigureCanvasQTAgg):
    """
    A custom Matplotlib canvas for embedding in a PyQt application.

    Attributes:
        axes (matplotlib.axes.Axes): The main axes of the figure.

    Methods:
        __init__(parent=None, width=5, height=4, dpi=100, fontsize=10):
            Initializes the MplCanvas with a figure and axes.
        
        _configure_axes(fontsize):
            Configures the appearance of the axes, including labels and tick parameters.
        
        _set_axes_colors():
            Sets the color of the axes spines to white.
    """
    def __init__(self, parent=None, width=5, height=4, dpi=100, fontsize=10):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self._configure_axes(fontsize)
        fig.subplots_adjust(left=0.05, right=0.95, top=1, bottom=0.1)
        fig.patch.set_facecolor('none')
        fig.patch.set_edgecolor('none')
        super().__init__(fig)

    def _configure_axes(self, fontsize):
        self.axes.tick_params(labelsize=fontsize)
        self.axes.set_xlabel('Event k', fontsize=fontsize, color='white')
        self.axes.set_ylabel('Time / µs', fontsize=fontsize, color='white')
        self.axes.set_facecolor('none')
        self.axes.tick_params(colors='white')
        self._set_axes_colors()

    def _set_axes_colors(self):
        self.axes.spines['top'].set_color('white')
        self.axes.spines['bottom'].set_color('white')
        self.axes.spines['left'].set_color('white')
        self.axes.spines['right'].set_color('white')

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize plot data
        self._initialize_plot_data()

        # Initialize UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Connect buttons to their respective slots
        self._connect_buttons()

        # Setup serial ports in combo box
        self.comports = self._setup_serial_ports()

        # Set up plot
        self._setup_plot()

        # Set up timer for updating
        self._setup_timer()

    def _initialize_plot_data(self):
        n_data = 50
        self.xdata = list(range(n_data))
        self.ydata = [random.randint(0, 10) for _ in range(n_data)]

    def _connect_buttons(self):
        self.ui.buttonStart.clicked.connect(say_hello)
        self.ui.buttonRefreshSerial.clicked.connect(self._setup_serial_ports)

    def _setup_serial_ports(self):
        com_ports = [[port.device, port.description] for port in list_ports.comports()]
        port_list = [item[0] for item in com_ports]
        self.ui.comboSerial.clear()
        self.ui.comboSerial.addItems(port_list)
        return com_ports

    def _setup_plot(self):
        self._plot_ref = None
        w = self.ui.widgetPlot.width()
        h = self.ui.widgetPlot.height()
        dpi = self.logicalDpiX()
        font_pixel_size = self.ui.widgetPlot.fontInfo().pixelSize()
        self._sc = MplCanvas(self, width=w, height=h, dpi=dpi, fontsize=font_pixel_size)
        self._initialize_plot()
        layout = QVBoxLayout(self.ui.widgetPlot)
        layout.addWidget(self._sc)

    def _initialize_plot(self):
        self._plot_ref = self._sc.axes.plot(self.xdata, self.ydata)
        self.ui.currentData.setEnabled(True)

    def _setup_timer(self):
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._update_plot)

    def _update_plot(self):
        # Update plot data
        self.ydata = self.ydata[1:] + [random.randint(0, 10)]
        self.xdata = self.xdata[1:] + [self.xdata[-1] + 1]
        self._plot_ref[0].set_data(self.xdata, self.ydata)
        self._plot_ref[0].axes.relim()
        self._plot_ref[0].axes.autoscale_view()
        self._sc.draw()

        # Update UI elements
        self.ui.currentData.display(self.ydata[-1])
        self.ui.lastData.insertItem(0, str(self.ydata[-1]))

        # Update timer interval
        self.timer.setInterval(random.randint(30, 500))




if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    widget.timer.start()
    sys.exit(app.exec())
