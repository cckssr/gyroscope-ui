import sys
import random
import re

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QToolButton, QStatusBar, QLabel
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from serial.tools import list_ports

from src.arduino import Arduino
from src.helper_classes import PlotWidget, Statusbar

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Initialize plot
        self.plot = PlotWidget(
            max_plot_points=50,
            width=self.ui.widgetPlot.width(),
            height=self.ui.widgetPlot.height(),
            dpi=self.logicalDpiX(),
            fontsize=self.ui.widgetPlot.fontInfo().pixelSize(),
            xlabel="Event k",
            ylabel="Time / µs"
        )
        QVBoxLayout(self.ui.widgetPlot).addWidget(self.plot)

        # Connect buttons to their respective slots
        self._connect_buttons()

        # Setup serial ports in combo box
        self._setup_serial_ports()

        # Set up timer for updating
        self._setup_timer()

        self.arduino = None

        # Statusbar
        self.statusbar = Statusbar(self.ui.statusBar)
        self.statusbar.temp_message("Ready")
        # self.ui.statusBar.showMessage("Ready")

        # self.sync_statusbar = QToolButton()
        # self.sync_statusbar.setObjectName("syncStatusbar")
        # self.sync_statusbar.setIcon(QIcon(QIcon.fromTheme(QIcon.ThemeIcon.NetworkWireless)))
        # self.sync_statusbar.setEnabled(False)
        # self.sync_statusbar.setStyleSheet("border: none;")
        # self.ui.statusBar.addPermanentWidget(self.sync_statusbar)

        # Check if demo mode is enabled
        self.ui.demoMode.toggled.connect(self._toggle_demo_mode)

    def _toggle_demo_mode(self, checked):
        if checked:
            print("Demo mode enabled")
            #self.update_statusbar_message("Demo mode enabled", "orange")
            self.statusbar.temp_message("Demo mode enabled", "orange")

            self.ui.comboSerial.addItem("/dev/ttymock", "Mock Serial Port")
            self.ui.comboSerial.setCurrentText("/dev/ttymock")
        else:
            print("Demo mode disabled")

    # def update_statusbar_message(self, message, backcolor, duration=None):
    #     old_message = self.ui.statusBar.currentMessage()
    #     old_style = self.ui.statusBar.styleSheet()
    #     self.ui.statusBar.setStyleSheet(f"background-color: {backcolor}")
    #     if duration:
    #         self.ui.statusBar.showMessage(message, duration)
    #         QTimer.singleShot(duration, lambda: self.ui.statusBar.setStyleSheet(old_style))
    #         QTimer.singleShot(duration, lambda: self.ui.statusBar.showMessage(old_message))
    #     else:
    #         self.ui.statusBar.showMessage(message)

    def _connect_buttons(self):
        self.ui.buttonRefreshSerial.clicked.connect(self._setup_serial_ports)
        self.ui.buttonConnect.clicked.connect(self._connect_device)

    def _setup_serial_ports(self):
        self.ui.comboSerial.clear()
        for port in list_ports.comports():
            self.ui.comboSerial.addItem(port.device, port.description)

    def _setup_timer(self):
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._update_plot)

    def _demo_update_plot(self):
        # Update plot data with random data
        randint = random.randint(100, 1000)/1000
        self.plot.update_plot(randint)

        # Update UI elements
        self.ui.currentData.display(int(randint*1000))
        self.ui.lastData.insertItem(0, str(int(randint*1000)))

        # QTimer.singleShot(100, lambda: self.sync_statusbar.setEnabled(True))
        # self.sync_statusbar.setEnabled(False)

        # Update timer interval
        self.timer.setInterval(randint)

    def _update_plot(self):
        pass

    def _connect_device(self):
        port = self.ui.comboSerial.currentText()
        if port == "/dev/ttymock":
            # self.statusbar.temp_message("Connected to Mock Serial Port", "green", 3000)
            self.statusbar.perm_message(f"Connected: {port}", 0)
            #self._initialize_plot()
            #self.sync_statusbar.setStyleSheet('background-color: green;')
            self.timer.timeout.connect(self._demo_update_plot)
        else:
            try:
                self.arduino = Arduino(port=port)
                self.arduino.reconnect()
                self.statusbar.perm_message(f"Connected: {port}", 0)
            except Exception as e:
                self.statusbar.temp_message(f"Error connecting to {port}: {e}", "red", 3000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    widget.timer.start()
    sys.exit(app.exec())
