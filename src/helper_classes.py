import matplotlib
import re
from threading import Thread, Event
from PySide6.QtWidgets import QStatusBar, QLabel, QMessageBox
from PySide6.QtCore import QTimer
from .arduino import Arduino

matplotlib.use("Qt5Agg")


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
                    value = random.randint(50, 1500)
                    # Callback mit dem generierten Wert
                    if self.data_callback:
                        self.data_callback(k, value)
                    k += 1
                    # Simulate processing time
                    time.sleep(value / 1000)
                else:
                    # Real data acquisition from Arduino
                    if self.arduino:
                        value = self.arduino.read_value()
                        # Callback nur wenn gültiger Wert
                        if value is not None and self.data_callback:
                            self.data_callback(k, value)
                            k += 1
            except Exception as e:
                if self.status_callback:
                    self.status_callback(f"Acquisition error: {e}", "red")
                break


class Statusbar:
    """
    A class to manage the status bar messages and styles.
    Attributes:
        statusbar (QStatusBar): The status bar widget.
        old_state (list): The previous state of the status bar.
    Methods:
        __init__(statusbar: QStatusBar):
            Initializes the Statusbar with the given QStatusBar widget.
        temp_message(message: str, backcolor: str = None, duration: int = None):
            Displays a temporary message on the status bar.
        perm_message(message: str, index: int = 0, backcolor: str = None):
            Displays a permanent message on the status bar.
        _update_statusbar_style(backcolor: str):
            Updates the style of the status bar.
        _save_state():
            Saves the current state of the status bar.
    """

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
            QTimer.singleShot(
                duration, lambda: self.statusbar.setStyleSheet(self.old_state[1])
            )
            QTimer.singleShot(
                duration, lambda: self.statusbar.showMessage(self.old_state[0])
            )
        else:
            self.statusbar.showMessage(message)

    def perm_message(self, message: str, index: int = 0, backcolor: str = None):
        new_style = self._update_statusbar_style(backcolor)
        self.statusbar.setStyleSheet(new_style)
        label = QLabel()
        label.setText(message)
        self.statusbar.insertPermanentWidget(index, label)

    def _update_statusbar_style(self, backcolor: str):
        # get current state
        self._save_state()

        # Set new style if backcolor is provided or keep the old style
        if backcolor:
            if "background-color:" in self.old_state[1]:
                # if old style had backcolor, replace it with the new one
                new_style = self.old_state[1].replace(
                    re.search(r"background-color:\s*[^;]+;", self.old_state[1]).group(
                        0
                    ),
                    f"background-color: {backcolor};",
                )
            else:
                # otherwise append the new backcolor
                new_style = self.old_state[1] + f"background-color: {backcolor};"
        else:
            new_style = self.old_state[1]
        return new_style

    def _save_state(self):
        self.old_state = [self.statusbar.currentMessage(), self.statusbar.styleSheet()]


class Helper:
    """
    A helper class with static methods for common tasks.
    Methods:
        close_event(parent, event):
            Handles the close event for a window.
    """

    @staticmethod
    def close_event(parent, event):
        reply = QMessageBox.question(
            parent,
            "Beenden",
            "Wollen Sie sicher das Programm schließen?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
