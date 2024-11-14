import sys
import random
import matplotlib

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PySide6.QtCore import Slot, QTimer
#from PySide6.QtGui import QIcon
from serial.tools import list_ports
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from src.arduino import Arduino

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_MainWindow

matplotlib.use('Qt5Agg')

MAX_DATA_POINTS = 50

# Greetings
@Slot()
def say_hello():
    print("Button clicked, Hello!")

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
    def __init__(self, width=5, height=4, dpi=100, fontsize=10):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self._configure_axes(fontsize, xlabel='Event k', ylabel='Time / µs')
        fig.subplots_adjust(left=0.08, right=0.95, top=1, bottom=0.1)
        fig.patch.set_facecolor('none')
        fig.patch.set_edgecolor('none')
        super().__init__(fig)

    def _configure_axes(self, fontsize, xlabel='x', ylabel='y'):
        self.axes.tick_params(labelsize=fontsize)
        self.axes.set_xlabel(xlabel, fontsize=fontsize, color='white')
        self.axes.set_ylabel(ylabel, fontsize=fontsize, color='white')
        self.axes.set_facecolor('none')
        self.axes.tick_params(colors='white')
        self._set_axes_colors()

    def _set_axes_colors(self, color='white'):
        self.axes.spines['top'].set_color(color)
        self.axes.spines['bottom'].set_color(color)
        self.axes.spines['left'].set_color(color)
        self.axes.spines['right'].set_color(color)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize plot data
        self._plot_ref = None
        self.xdata = None
        self.ydata = None
        self._initialize_plot_data()

        # Initialize UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Connect buttons to their respective slots
        self._connect_buttons()

        # Setup serial ports in combo box
        self._setup_serial_ports()

        # Set up plot
        self._setup_plot()

        # Set up timer for updating
        self._setup_timer()

        # Statusbar
        self.ui.statusBar.showMessage("Ready")

        # Check if demo mode is enabled
        self.ui.demoMode.toggled.connect(self._toggle_demo_mode)

    def _toggle_demo_mode(self, checked):
        if checked:
            print("Demo mode enabled")
            self.update_statusbar_message("Demo mode enabled", "orange")
            self.ui.comboSerial.addItem("/dev/ttymock", "Mock Serial Port")
            self.ui.comboSerial.setCurrentText("/dev/ttymock")
        else:
            print("Demo mode disabled")

    def update_statusbar_message(self, message, backcolor, duration=None):
        old_message = self.ui.statusBar.currentMessage()
        old_style = self.ui.statusBar.styleSheet()
        self.ui.statusBar.setStyleSheet(f"background-color: {backcolor}")
        if duration:
            self.ui.statusBar.showMessage(message, duration)
            QTimer.singleShot(duration, lambda: self.ui.statusBar.setStyleSheet(old_style))
            QTimer.singleShot(duration, lambda: self.ui.statusBar.showMessage(old_message))
        else:
            self.ui.statusBar.showMessage(message)

    def _connect_buttons(self):
        self.ui.buttonStart.clicked.connect(say_hello)
        self.ui.buttonRefreshSerial.clicked.connect(self._setup_serial_ports)
        self.ui.buttonConnect.clicked.connect(self._connect_device)

    def _setup_serial_ports(self):
        self.ui.comboSerial.clear()
        for port in list_ports.comports():
            self.ui.comboSerial.addItem(port.device, port.description)
        #com_ports = [[port.device, port.description] for port in list_ports.comports()]
        #port_list = [item[0] for item in com_ports]

        #self.ui.comboSerial.addItems(com_ports)
        #return com_ports

    def _initialize_plot_data(self):
        self.xdata = [0]
        self.ydata = [0]

    def _setup_plot(self):
        self._plot_ref = None
        w = self.ui.widgetPlot.width()
        h = self.ui.widgetPlot.height()
        dpi = self.logicalDpiX()
        font_pixel_size = self.ui.widgetPlot.fontInfo().pixelSize()
        self._sc = MplCanvas(width=w, height=h, dpi=dpi, fontsize=font_pixel_size)
        layout = QVBoxLayout(self.ui.widgetPlot)
        layout.addWidget(self._sc)

    def _initialize_plot(self):
        self._plot_ref = self._sc.axes.plot(self.xdata, self.ydata)
        self.ui.currentData.setEnabled(True)

    def _setup_timer(self):
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._update_plot)

    def _demo_update_plot(self):
        # Update plot data        
        self.xdata = self.xdata[-MAX_DATA_POINTS:] + [self.xdata[-1] + 1]
        self.ydata = self.ydata[-MAX_DATA_POINTS:] + [random.randint(50, 500)]
        self._plot_ref[0].set_data(self.xdata, self.ydata)
        self._plot_ref[0].axes.relim()
        self._plot_ref[0].axes.autoscale_view()
        self._sc.draw()

        # Update UI elements
        self.ui.currentData.display(self.ydata[-1])
        self.ui.lastData.insertItem(0, str(self.ydata[-1]))

        # Update timer interval
        self.timer.setInterval(self.ydata[-1])

    def _update_plot(self):
        pass

    def _connect_device(self):
        port = self.ui.comboSerial.currentText()
        if port == "/dev/ttymock":
            self.arduino = None
            self.update_statusbar_message("Connected to Mock Serial Port", "green", 3000)
            self._initialize_plot()
            self.timer.timeout.connect(self._demo_update_plot)
        else:
            try:
                self.arduino = Arduino(port=port)
                self.arduino.reconnect()
                self.update_statusbar_message(f"Connected to {port}", "green", 3000)
            except Exception as e:
                self.update_statusbar_message(f"Error connecting to {port}: {e}", "red", 3000)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    widget.timer.start()
    sys.exit(app.exec())
