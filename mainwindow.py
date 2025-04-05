import sys
import random
import time
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QDialog,
    QWidget,
    QMessageBox,
    QDialogButtonBox,
)
from PySide6.QtCore import QTimer, Signal, QObject
from serial.tools import list_ports
from threading import Thread, Event
from src.arduino import Arduino
from src.helper_classes import PlotWidget, Statusbar, Helper
from ui_form import Ui_MainWindow
from ui_alert import Ui_Dialog
from ui_control import Ui_Form
from ui_connection import Ui_Dialog as Ui_Connection


class DeviceManager:
    """
    Manages device connections and data acquisition.
    Separates hardware logic from UI components.
    """

    def __init__(self, status_callback=None, data_callback=None):
        self.arduino = None
        self.connected = False
        self.port = None
        self.status_callback = status_callback
        self.data_callback = data_callback
        self.running = False
        self.stop_event = Event()
        self.acquire_thread = None

    def connect(self, port):
        """
        Connects to the specified device port.

        Args:
            port (str): The port to connect to

        Returns:
            bool: True if connection successful, False otherwise
        """
        self.port = port

        if port == "/dev/ttymock":
            if self.status_callback:
                self.status_callback(f"Connected to mock device: {port}", "orange")
            self.connected = True
            return True

        try:
            self.arduino = Arduino(port=port)
            self.arduino.reconnect()
            if self.status_callback:
                self.status_callback(f"Connected: {port}", "green")
            self.connected = True
            return True

        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Error connecting to {port}: {e}", "red")
            self.connected = False
            return False

    def start_acquisition(self):
        """
        Starts the data acquisition thread.
        """
        if not self.connected:
            return False

        self.stop_event.clear()
        self.running = True
        self.acquire_thread = Thread(target=self._acquisition_loop)
        self.acquire_thread.daemon = True
        self.acquire_thread.start()
        return True

    def stop_acquisition(self):
        """
        Stops the data acquisition thread.
        """
        self.running = False
        self.stop_event.set()
        if self.acquire_thread and self.acquire_thread.is_alive():
            self.acquire_thread.join(timeout=1.0)

    def _acquisition_loop(self):
        """
        Main acquisition loop that runs in a separate thread.
        For mock device, generates random data.
        For real device, reads from Arduino.
        """
        k = 0
        while self.running and not self.stop_event.is_set():
            try:
                if self.port == "/dev/ttymock":
                    # Mock data generation
                    value = random.randint(100, 1000)
                    # Simulate processing time
                    time.sleep(1 / value)
                else:
                    # Real data acquisition from Arduino
                    if self.arduino:
                        value = (
                            self.arduino.read_value()
                        )  # Implement this in Arduino class
                    else:
                        value = 0

                if self.data_callback:
                    self.data_callback(k, value)
                k += 1
            except Exception as e:
                if self.status_callback:
                    self.status_callback(f"Acquisition error: {e}", "red")
                break


class DataController:
    """
    Manages measurement data and plot updates.
    """

    def __init__(self, plot_widget, display_widget=None, history_widget=None):
        self.plot = plot_widget
        self.display = display_widget
        self.history = history_widget
        self.data_points = []
        self.max_history = 100

    def add_data_point(self, index, value):
        """
        Adds a new data point and updates UI elements.

        Args:
            index (int): The x-value (usually a counter)
            value (float): The measured value
        """
        self.data_points.append((index, value))
        if len(self.data_points) > self.max_history:
            self.data_points.pop(0)

        # Update plot
        if self.plot:
            self.plot.update_plot((index, value))

        # Update current value display
        if self.display:
            self.display.display(value)

        # Update history list
        if self.history:
            self.history.insertItem(0, f"{index}: {value}")
            while self.history.count() > self.max_history:
                self.history.takeItem(self.history.count() - 1)

    def clear_data(self):
        """
        Clears all data points and resets UI elements.
        """
        self.data_points = []
        if self.plot:
            self.plot.clear()
        if self.history:
            self.history.clear()


class ControlWindow(QWidget):
    def __init__(self, parent=None):
        """
        Initializes the control window.
        """
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)


class ConnectionWindow(QDialog):
    def __init__(self, parent=None):
        """
        Initializes the connection window.
        """
        self.mock_port = [
            "/dev/ttymock",
            "Mock Device",
            "Virtual device for demonstration purposes",
        ]
        self.demoMode = True
        self.device_manager = DeviceManager(status_callback=self.status_message)
        self.connection_successful = False

        super().__init__(parent)
        self.ui = Ui_Connection()
        self.ui.setupUi(self)
        self.combo = self.ui.comboSerial
        self._update_ports()

        self.ui.buttonRefreshSerial.clicked.connect(self._update_ports)
        self.combo.currentIndexChanged.connect(self._update_port_description)

        # Status message (may need to be added to UI)
        if not hasattr(self.ui, "statusLabel"):
            from PySide6.QtWidgets import QLabel

            self.ui.statusLabel = QLabel("Select a device and click OK to connect")
            if hasattr(self.ui, "verticalLayout"):
                self.ui.verticalLayout.addWidget(self.ui.statusLabel)

    def status_message(self, message, color="black", timeout=0):
        """
        Updates the status message in the connection dialog.
        """
        if hasattr(self.ui, "statusLabel"):
            self.ui.statusLabel.setText(message)
            self.ui.statusLabel.setStyleSheet(f"color: {color};")
            QApplication.processEvents()  # Process events to update UI immediately

    def _update_ports(self):
        """
        Initializes and updates the available serial ports.
        """
        # Clear existing ports
        self.ui.comboSerial.clear()
        for field in [self.ui.device_name, self.ui.device_address, self.ui.device_desc]:
            field.clear()

        # Get available ports
        self.ports = list_ports.comports()
        for port in self.ports:
            self.combo.addItem(port.device, port.description)

        # Add mock port if demo mode is active
        if self.demoMode:
            self.combo.addItem(self.mock_port[0], self.mock_port[1])

    def _update_port_description(self):
        """
        Updates the port description based on the selected port.
        """
        index = self.combo.currentIndex()
        # Check if demo mode is active and set mock port details
        if self.demoMode and index == self.combo.count() - 1:
            self.ui.device_name.setText(self.mock_port[1])
            self.ui.device_address.setText(self.mock_port[0])
            self.ui.device_desc.setText(self.mock_port[2])
            return
        # check if index is valid
        elif index >= 0:
            port = self.ports[index]
            self.ui.device_name.setText(port.name)
            self.ui.device_address.setText(port.device)
            self.ui.device_desc.setText(port.description)
        # If no valid index, clear the fields
        else:
            for field in [
                self.ui.device_name,
                self.ui.device_address,
                self.ui.device_desc,
            ]:
                field.clear()

    def attempt_connection(self):
        """
        Attempts to connect to the selected device.

        Returns:
            tuple: (success, device_manager) - success is a boolean, device_manager is the
                  configured DeviceManager if successful, None otherwise.
        """
        port = self.combo.currentText()
        self.status_message(f"Connecting to {port}...", "blue")

        # Try to connect
        success = self.device_manager.connect(port)

        if success:
            self.status_message(f"Successfully connected to {port}", "green")
            self.connection_successful = True
            return True, self.device_manager
        else:
            self.connection_successful = False
            return False, None

    def accept(self):
        """
        Called when the user clicks OK. Attempts connection before accepting.
        """
        success, _ = self.attempt_connection()

        if success:
            return super().accept()
        else:
            # Show error dialog with retry options
            error_msg = f"Failed to connect to {self.combo.currentText()}"
            alert = AlertWindow(
                self,
                message=f"{error_msg}\n\nPlease check if the device is connected properly and try again.",
                title="Connection Error",
                buttons=[
                    ("Retry", QDialogButtonBox.RetryRole),
                    ("Select Another Port", QDialogButtonBox.ActionRole),
                    ("Cancel", QDialogButtonBox.RejectRole),
                ],
            )

            alert_result = alert.exec()

            # Handle user choice
            if hasattr(alert.ui, "buttonBox"):
                clicked_button = alert.ui.buttonBox.clickedButton()
                button_role = alert.ui.buttonBox.buttonRole(clicked_button)

                if button_role == QDialogButtonBox.RejectRole:  # Cancel
                    # Reject the dialog, which will terminate the application in the main loop
                    return super().reject()

                elif button_role == QDialogButtonBox.ActionRole:  # Select Another Port
                    # Just keep the dialog open to let user select another port
                    return

                elif button_role == QDialogButtonBox.RetryRole:  # Retry
                    # Try again with the same port
                    self.accept()

            return False


class AlertWindow(QDialog):
    """
    Initializes the alert window with customizable buttons and messages.
    """

    def __init__(self, parent=None, message="Alert", title="Warning", buttons=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(title)

        # Set message if the UI has a message label
        if hasattr(self.ui, "labelMessage"):
            self.ui.labelMessage.setText(message)

        # Configure buttons if provided
        if buttons and hasattr(self.ui, "buttonBox"):
            self.ui.buttonBox.clear()
            for button_text, role in buttons:
                self.ui.buttonBox.addButton(button_text, role)


class MainWindow(QMainWindow):
    def __init__(self, device_manager, parent=None):
        """
        Initializes the main window and all components of the application.
        Sets up the UI, initializes data structures, and prepares connections.

        Args:
            device_manager (DeviceManager): Already connected device manager
            parent: Parent widget
        """
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Create status bar first for early feedback
        self.statusbar = Statusbar(self.ui.statusBar)
        self.statusbar.temp_message("Initializing application...")

        # Use the provided device manager
        self.device_manager = device_manager
        self.device_manager.data_callback = self.handle_data
        self.device_manager.status_callback = self.statusbar.temp_message

        # Setup plot widget
        self.plot = PlotWidget(
            max_plot_points=50,
            width=self.ui.widgetPlot.width(),
            height=self.ui.widgetPlot.height(),
            dpi=self.logicalDpiX(),
            fontsize=self.ui.widgetPlot.fontInfo().pixelSize(),
            xlabel="Event k",
            ylabel="Time / µs",
        )
        QVBoxLayout(self.ui.widgetPlot).addWidget(self.plot)

        # Setup data controller
        self.data_controller = DataController(
            plot_widget=self.plot,
            display_widget=self.ui.currentData,
            history_widget=self.ui.lastData,
        )

        # Initialize UI components
        self.cwindow = self._setup_control()
        self.measurement = False
        self._setup_buttons()
        self._setup_timer()

        # Connect signals
        if hasattr(self.ui, "demoMode"):
            self.ui.demoMode.toggled.connect(self._toggle_demo_mode)

        # Initialize the current connected port display if available
        if hasattr(self.ui, "labelConnectedPort"):
            self.ui.labelConnectedPort.setText(
                f"Connected to: {self.device_manager.port}"
            )

        self.statusbar.temp_message(
            f"Connected to {self.device_manager.port}. Ready to start measurements.",
            "green",
        )

    def handle_data(self, index, value):
        """
        Handles incoming data from the device.
        Updates display, history, and plot.

        Args:
            index (int): The data point index
            value (float): The measured value
        """
        self.data_controller.add_data_point(index, value)

    def _open_alert(self):
        """
        Opens the alert window.
        """
        alert = AlertWindow(self)
        alert.exec()

    def _update_measurement(self, checked: bool):
        """
        Updates the measurement status based on the given value.
        """
        self.measurement = checked
        if checked:
            self.ui.buttonStart.setEnabled(False)
            self.ui.buttonStop.setEnabled(True)
            self.device_manager.start_acquisition()
        else:
            self.ui.buttonStart.setEnabled(True)
            self.ui.buttonStop.setEnabled(False)
            self.device_manager.stop_acquisition()

    def _toggle_demo_mode(self, checked: bool):
        """
        Toggles the demo mode based on the given value.
        """
        if checked:
            self.statusbar.temp_message("Demo mode enabled", "orange")
            self.ui.comboSerial.addItem("/dev/ttymock", "Mock Serial Port")
            self.ui.comboSerial.setCurrentText("/dev/ttymock")
        else:
            print("Demo mode disabled")

    def _setup_control(self) -> ControlWindow:
        """
        Sets up the control window.
        """
        cwindow = ControlWindow()
        w, h = cwindow.width(), cwindow.height()
        cwindow.setGeometry(0, 0, w, h)
        cwindow.show()
        self.ui.controlWindow.setChecked(True)
        return cwindow

    def _setup_buttons(self):
        """
        Connects the buttons to their respective functions.
        """
        # self.ui.buttonRefreshSerial.clicked.connect(self._open_alert)
        # # Update the Connect button to use the existing connection or reconnect if needed
        # if hasattr(self.ui, 'buttonConnect'):
        #     self.ui.buttonConnect.clicked.connect(self._reconnect_device)
        self.ui.buttonStart.clicked.connect(lambda: self._update_measurement(True))
        self.ui.buttonStop.clicked.connect(lambda: self._update_measurement(False))

    def _reconnect_device(self):
        """
        Shows the connection dialog again to reconnect or change the device.
        """
        connection_dialog = ConnectionWindow(self)
        if connection_dialog.exec():
            success, new_device_manager = connection_dialog.attempt_connection()
            if success:
                # Stop any existing measurements
                if self.measurement:
                    self._update_measurement(False)

                # Update the device manager
                self.device_manager = new_device_manager
                self.device_manager.data_callback = self.handle_data
                self.device_manager.status_callback = self.statusbar.temp_message

                self.statusbar.temp_message(
                    f"Reconnected to {self.device_manager.port}", "green"
                )

                # Update the port display if available
                if hasattr(self.ui, "labelConnectedPort"):
                    self.ui.labelConnectedPort.setText(
                        f"Connected to: {self.device_manager.port}"
                    )

    def _setup_timer(self):
        """
        Sets up the timer.
        """
        self.timer = QTimer()
        self.timer.setInterval(100)

    def closeEvent(self, event):
        """
        Handles the window close event.
        Ensures all threads are stopped before closing.
        """
        # Stop any running measurements/threads
        if self.measurement:
            self.device_manager.stop_acquisition()

        # Stop the timer if it's running
        if self.timer.isActive():
            self.timer.stop()

        # Close the control window
        if self.cwindow:
            self.cwindow.close()

        # Ensure the application completely exits
        QApplication.quit()

        # Accept the close event
        event.accept()


if __name__ == "__main__":
    """
    Starts the application.
    """
    app = QApplication(sys.argv)

    # Make sure application exits properly when main window is closed
    app.setQuitOnLastWindowClosed(True)

    # Show connection dialog first
    connection_dialog = ConnectionWindow()

    # If connection dialog is accepted (OK clicked), attempt to connect
    if connection_dialog.exec():
        success, device_manager = connection_dialog.attempt_connection()

        if success:
            # Create and show main window only if connection was successful
            main_window = MainWindow(device_manager)
            main_window.show()
            main_window.timer.start()

            # Run the application
            sys.exit(app.exec())
        else:
            # This should not happen normally as accept() in ConnectionWindow
            # only returns True if connection was successful, but handle it just in case
            QMessageBox.critical(
                None,
                "Connection Error",
                "Failed to connect to the device. Application will exit.",
            )
            sys.exit(1)
    else:
        # User cancelled the connection dialog
        print("Connection cancelled by user")
        sys.exit(0)
