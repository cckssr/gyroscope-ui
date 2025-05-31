import random
import time
from threading import Thread, Event
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QDialogButtonBox,
)
from serial.tools import list_ports
from pyqt.ui_connection import Ui_Dialog as Ui_Connection
from src.helper_classes import AlertWindow
from src.arduino import Arduino, GMCounter
from src.debug_utils import Debug


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

    def status_message(self, message, color="white", timeout=0):
        """
        Updates the status message in the connection dialog.
        """
        self.ui.status_msg.setText(message)
        self.ui.status_msg.setStyleSheet(f"color: {color};")
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
        arduino_index = -1

        for i, port in enumerate(self.ports):
            self.combo.addItem(port.device, port.description)
            # Prüfen, ob in der Beschreibung "UNO" vorkommt und es das erste ist
            if "UNO" in port.description and arduino_index == -1:
                arduino_index = i

        # Add mock port if demo mode is active
        if self.demoMode:
            self.combo.addItem(self.mock_port[0], self.mock_port[1])

        # Setze Arduino-Port als vorausgewählt, wenn gefunden
        if arduino_index != -1:
            self.combo.setCurrentIndex(arduino_index)
            self._update_port_description()

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


class DeviceManager:
    """
    Manages device connections and data acquisition.
    Separates hardware logic from UI components.
    """

    def __init__(self, status_callback=None, data_callback=None):
        """
        Initialize the DeviceManager.

        Args:
            status_callback (Callable[[str, str, int], None], optional): Callback for status messages.
                Function that takes message text, color, and timeout.
            data_callback (Callable[[int, float], None], optional): Callback for data updates.
                Function that takes the index and value of new data points.
        """
        self.arduino = None
        self.connected: bool = False
        self.port: str = None
        self.status_callback = status_callback
        self.data_callback = data_callback
        self.running: bool = False
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
        Debug.info(f"Attempting to connect to device on port: {port}")

        if port == "/dev/ttymock":
            Debug.info(f"Using mock device on port: {port}")
            if self.status_callback:
                self.status_callback(f"Verbunden mit Mock-Gerät: {port}", "orange")
            self.connected = True
            return True

        try:
            # Try to connect to GM counter first for better functionality
            try:
                Debug.info(
                    f"Attempting to connect as GM counter device on port: {port}"
                )
                self.arduino = GMCounter(port=port)
                if self.status_callback:
                    self.status_callback(f"GM-Zähler verbunden an {port}", "green")
                Debug.info(f"Successfully connected to GM counter on port: {port}")
            except Exception as e:
                # Fall back to basic Arduino connection
                Debug.info(
                    f"Failed to connect as GM counter, trying basic Arduino: {e}"
                )
                self.arduino = Arduino(port=port)
                if self.status_callback:
                    self.status_callback(f"Arduino verbunden an {port}", "green")
                Debug.info(f"Connected to basic Arduino on port: {port}")

            self.arduino.reconnect()
            self.connected = True
            return True

        except Exception as e:
            Debug.error(f"Failed to connect to device on {port}: {e}", exc_info=True)
            if self.status_callback:
                self.status_callback(f"Fehler beim Verbinden mit {port}: {e}", "red")
            self.connected = False
            return False

    def start_acquisition(self):
        """
        Starts the data acquisition thread.
        """
        if not self.connected:
            Debug.error("Cannot start acquisition: device not connected")
            return False

        Debug.info("Starting data acquisition")
        self.stop_event.clear()
        self.running = True
        self.acquire_thread = Thread(target=self._acquisition_loop)
        self.acquire_thread.daemon = True
        self.acquire_thread.start()
        Debug.debug(f"Acquisition thread started: {self.acquire_thread.name}")
        return True

    def stop_acquisition(self):
        """
        Stops the data acquisition thread.
        """
        Debug.info("Stopping data acquisition")
        self.running = False
        self.stop_event.set()
        if self.acquire_thread and self.acquire_thread.is_alive():
            Debug.debug(
                f"Waiting for acquisition thread to terminate: {self.acquire_thread.name}"
            )
            self.acquire_thread.join(timeout=1.0)
            if self.acquire_thread.is_alive():
                Debug.info(
                    f"Acquisition thread did not terminate within timeout: {self.acquire_thread.name}"
                )

    def _acquisition_loop(self):
        """
        Main acquisition loop that runs in a separate thread.
        For mock device, generates random data.
        For real device, reads from Arduino.
        """
        k = 0
        Debug.info("Starting data acquisition loop")
        while self.running and not self.stop_event.is_set():
            try:
                if self.port == "/dev/ttymock":
                    # Mock data generation
                    value = random.randint(50, 1500)
                    Debug.debug(f"Generated mock value: {value}")
                    # Callback mit dem generierten Wert
                    if self.data_callback:
                        self.data_callback(k, value)
                    k += 1
                    # Simulate processing time
                    time.sleep(value / 1000)
                else:
                    # Real data acquisition from Arduino
                    if self.arduino:
                        # Check if we have a GM counter or just a basic Arduino
                        if hasattr(self.arduino, "get_data"):
                            # For GM counter, get full data and extract relevant values
                            Debug.debug("Reading data from GM counter")
                            data = self.arduino.get_data()
                            # Use last_count as the value to display
                            value = data.get("last_count", 0)
                            Debug.debug(f"Received GM counter value: {value}")
                            # Also use arduino send_command to send the stream command if it's a GM counter
                            self.arduino.set_stream(3)
                        else:
                            # Basic Arduino read
                            Debug.debug("Reading data from basic Arduino")
                            value = self.arduino.read_value()
                            Debug.debug(f"Received Arduino value: {value}")

                        # Try to convert string to number if needed
                        if isinstance(value, str):
                            try:
                                value = float(value)
                                Debug.debug(f"Converted string to number: {value}")
                            except (ValueError, TypeError) as e:
                                Debug.error(f"Could not convert value to number: {e}")

                        # Callback nur wenn gültiger Wert
                        if value is not None and self.data_callback:
                            self.data_callback(k, value)
                            k += 1

            except Exception as e:
                Debug.error(f"Error in acquisition loop: {e}", exc_info=True)
                if self.status_callback:
                    self.status_callback(f"Messfehler: {e}", "red")
                break

        Debug.info("Acquisition loop terminated")
