#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import time
from typing import Union, Dict
from threading import Thread, Event
from PySide6.QtWidgets import QWidget  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QDialogButtonBox,
)
from serial.tools import list_ports
from pyqt.ui_connection import Ui_Dialog as Ui_Connection
from src.helper_classes import AlertWindow
from src.arduino import GMCounter
from src.debug_utils import Debug


class ConnectionWindow(QDialog):
    def __init__(
        self,
        parent: QWidget = None,
        demo_mode: bool = False,
    ):
        """
        Initializes the connection window.

        Args:
            parent (QWidget, optional): Parent widget for the dialog. Defaults to None.
            demo_mode (bool, optional): If True, uses a mock port for demonstration purposes.
        """
        self.device_manager = DeviceManager(status_callback=self.status_message)
        self.connection_successful = False
        self.demo_mode = demo_mode
        self.mock_port = [
            "/dev/ttymock",
            "Mock Device",
            "Virtual device for demonstration purposes",
        ]

        # Initialize parent and connection windows
        super().__init__(parent)
        self.ui = Ui_Connection()
        self.ui.setupUi(self)
        self.combo = self.ui.comboSerial  # Use the combo box from the UI
        self._update_ports()  # Initialize available ports

        # Attach functions to UI elements
        self.ui.buttonRefreshSerial.clicked.connect(self._update_ports)
        self.combo.currentIndexChanged.connect(self._update_port_description)

    def status_message(self, message, color="white"):
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
        if self.demo_mode:
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
        if self.demo_mode and index == self.combo.count() - 1:
            name = self.mock_port[1]
            address = self.mock_port[0]
            description = self.mock_port[2]
            return
        # check if index is valid
        elif index >= 0:
            port = self.ports[index]
            name = port.name
            address = port.device
            description = port.description
        # If no valid index, clear the fields
        else:
            name = ""
            address = ""
            description = ""

        self.ui.device_name.setText(name)
        self.ui.device_address.setText(address)
        self.ui.device_desc.setText(description)

    def attempt_connection(self):
        """
        Attempts to connect to the selected device.

        Returns:
            tuple: (success, device_manager) - success is a boolean, device_manager is the
                  configured DeviceManager if successful, None otherwise.
        """
        port = self.combo.currentText()
        self.status_message(f"Connecting to {port}...", "blue")
        Debug.info(f"ConnectionWindow: Attempting to connect to port: {port}")

        # Check if connected
        success = self.device_manager.connect(port)

        if success:
            self.status_message(f"Successfully connected to {port}", "green")
            Debug.info(f"Successfully connected to port: {port}")
            self.connection_successful = True
            return True, self.device_manager
        else:
            Debug.error(f"Failed to connect to port: {port}")
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
            Debug.error(
                f"Connection attempt failed for port: {self.combo.currentText()}"
            )
            exit(1)  # Exit the application with an error code

            # Show error dialog with retry options TODO: Correct alert dialog
            # error_msg = f"Failed to connect to {self.combo.currentText()}"
            # alert = AlertWindow(
            #     self,
            #     message=f"{error_msg}\n\nPlease check if the device is connected properly and try again.",
            #     title="Connection Error",
            #     buttons=[
            #         ("Retry", QDialogButtonBox.ButtonRole.ResetRole),
            #         ("Select Another Port", QDialogButtonBox.ButtonRole.ActionRole),
            #         ("Cancel", QDialogButtonBox.ButtonRole.RejectRole),
            #     ],
            # )

            # alert.exec()

            # # Handle user choice
            # if hasattr(alert.ui, "buttonBox"):
            #     clicked_button = alert.ui.buttonBox.
            #     button_role = alert.ui.buttonBox.buttonRole(clicked_button)
            #     if button_role == QDialogButtonBox.ButtonRole.RejectRole:  # Cancel
            #         # Reject the dialog, which will terminate the application in the main loop
            #         return super().reject()

            #     elif (
            #         button_role == QDialogButtonBox.ButtonRole.ActionRole
            #     ):  # Select Another Port
            #         # Just keep the dialog open to let user select another port
            #         return

            #     elif button_role == QDialogButtonBox.ButtonRole.ResetRole:  # Retry
            #         # Try again with the same port
            #         self.accept()

            # return False


class DeviceManager:
    """
    Manages device connections and data acquisition.
    Separates hardware logic from UI components.

    Implementiert das Delegationsmuster für die Kommunikation mit dem Arduino/GM-Zähler.
    Anstatt Methoden zu duplizieren oder von Arduino zu erben, leitet dieser Manager
    alle Gerätebefehle an die entsprechende Instanz weiter.
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
        self.device: GMCounter  # Geräteobjekt (GMCounter)
        self.connected: bool = False
        self.port: str = "None"
        self.is_gm_counter: bool = False
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
        Debug.info(f"DeviceManager: Attempting to connect to device on port: {port}")

        if port == "/dev/ttymock":
            Debug.info(f"Using mock device on port: {port}")
            if self.status_callback:
                self.status_callback(f"Verbunden mit Mock-Gerät: {port}", "orange")
            self.connected = True
            self.is_gm_counter = False
            return True

        try:
            # GM-Counter ist obligatorisch, kein Fallback mehr auf einfachen Arduino
            Debug.info(f"Attempting to connect to GM counter device on port: {port}")
            self.device: GMCounter = GMCounter(port=port)
            self.is_gm_counter = True

            if self.device and self.device.connected:
                self.connected = True

                if self.status_callback:
                    self.status_callback(f"GM-Zähler verbunden an {port}", "green")
                Debug.info(f"Successfully connected to GM counter on port: {port}")
                return True
            else:
                Debug.error(f"Failed to initialize GM counter on {port}")
                self.connected = False
                return False

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
        if not self.is_connected():
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

    def _generate_mock_data(self, index: int) -> tuple:
        """
        Generiert Mock-Daten für den Demo-Modus.

        Args:
            index: Der aktuelle Index für die Callback-Funktion

        Returns:
            tuple: (neuer_index, Wartezeit)
        """
        value = random.randint(50, 1500)
        Debug.debug(f"Generated mock value: {value}")

        if self.data_callback:
            self.data_callback(index, value)

        # Simulate processing time and return wait time
        wait_time = value / 1000
        return index + 1, wait_time

    # def _read_from_gm_counter(self) -> Union[int, float, None]:
    #     """
    #     Liest Daten vom GM-Zähler.

    #     Returns:
    #         Union[int, float, None]: Der gelesene Wert oder None bei Fehler
    #     """
    #     Debug.debug("Reading data from GM counter")

    #     if self.device is None:
    #         return None

    #     # Wir wissen, dass das Gerät ein GMCounter ist
    #     data = self.device.get_data()
    #     value = data.get("last_count", 0)
    #     Debug.debug(f"Received GM counter value: {value}")

    #     # Auch Stream-Modus setzen
    #     self.device.set_stream(3)
    #     return value

    # Methode _read_from_arduino entfernt, da nur noch GM-Counter unterstützt werden

    def _convert_value_if_needed(
        self, value: Union[int, float, str, None]
    ) -> Union[int, float, str, None]:
        """
        Konvertiert Zeichenketten in Zahlen, wenn nötig.

        Args:
            value: Der zu konvertierende Wert

        Returns:
            Union[int, float, str, None]: Der konvertierte Wert oder der ursprüngliche Wert
        """
        if value is None:
            return None

        if isinstance(value, str):
            try:
                converted = float(value)
                Debug.debug(f"Converted string to number: {converted}")
                return converted
            except (ValueError, TypeError) as e:
                Debug.error(f"Could not convert value to number: {e}")

        return value

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
                # Mock-Modus
                if self.port == "/dev/ttymock":
                    k, wait_time = self._generate_mock_data(k)
                    time.sleep(wait_time)
                    continue

                # Echtes Gerät
                if not self.is_connected():
                    time.sleep(1.0)  # Warte und prüfe erneut
                    continue

                # Lesen vom GM-Counter (nur dieser wird unterstützt)
                value = self._read_from_gm_counter()

                if value is None:
                    time.sleep(0.5)
                    continue

                # Konvertiere und sende den Wert
                converted_value = self._convert_value_if_needed(value)

                # Callback nur wenn gültiger Wert
                if converted_value is not None and self.data_callback:
                    self.data_callback(k, converted_value)
                    k += 1

            except Exception as e:
                Debug.error(f"Error in acquisition loop: {e}", exc_info=True)
                if self.status_callback:
                    self.status_callback(f"Messfehler: {e}", "red")
                break

        Debug.info("Acquisition loop terminated")

    # #
    # # Delegierte Methoden für einheitlichen Gerätezugriff
    # #

    # def send_command(self, command: str) -> bool:
    #     """
    #     Sendet einen Befehl an das verbundene Gerät.

    #     Args:
    #         command: Der zu sendende Befehl

    #     Returns:
    #         bool: True bei Erfolg, False sonst
    #     """
    #     if not self.is_connected():
    #         Debug.error("Cannot send command: no device connected")
    #         return False

    #     return self.device.send_command(command)

    # def read_value(self) -> Union[int, float, str, None]:
    #     """
    #     Liest einen Wert vom verbundenen Gerät.

    #     Returns:
    #         Union[int, float, str, None]: Der gelesene Wert oder None bei Fehler
    #     """
    #     if not self.is_connected():
    #         Debug.error("Cannot read value: no device connected")
    #         return None

    #     return self.device.read_value()

    # def get_data(self) -> Dict[str, Union[int, bool]]:
    #     """
    #     Extrahiert Daten vom GM-Zähler.

    #     Returns:
    #         dict: Ein Dictionary mit den extrahierten Daten.
    #     """
    #     if not self.is_connected():
    #         return {}

    #     return self.device.get_data()

    # def set_stream(self, value: int = 0) -> bool:
    #     """
    #     Setzt den Stream-Modus des GM-Zählers.

    #     Args:
    #         value: Der Stream-Modus (0-3)

    #     Returns:
    #         bool: True bei Erfolg, False sonst
    #     """
    #     if not self.is_connected():
    #         return False

    #     self.device.set_stream(value)
    #     return True

    # def set_counting(self, value: bool = False) -> bool:
    #     """
    #     Aktiviert oder deaktiviert den Zählmodus des GM-Zählers.

    #     Args:
    #         value: True zum Aktivieren, False zum Deaktivieren

    #     Returns:
    #         bool: True bei Erfolg, False sonst
    #     """
    #     if not self.is_connected():
    #         return False

    #     self.device.set_counting(value)
    #     return True

    # def set_voltage(self, value: int = 500) -> bool:
    #     """
    #     Setzt die Spannung des GM-Zählers.

    #     Args:
    #         value: Die Spannung in Volt (meist 400-900)

    #     Returns:
    #         bool: True bei Erfolg, False sonst
    #     """
    #     if not self.is_connected():
    #         return False

    #     self.device.set_voltage(value)
    #     return True

    # def get_information(self) -> Dict[str, str]:
    #     """
    #     Ruft Informationen vom GM-Zähler ab.

    #     Returns:
    #         Dict[str, str]: Ein Dictionary mit Geräteinformationen
    #     """
    #     if not self.is_connected():
    #         return {}

    #     return self.device.get_information()

    def is_connected(self) -> bool:
        """
        Prüft die Verbindung zum Gerät.

        Returns:
            bool: True, wenn das Gerät verbunden ist, False sonst

        Notes:
            Bei False gibt die Methode automatisch eine entsprechende Fehlermeldung aus.
        """
        if not self.device:
            Debug.error("Kein Gerät vorhanden")
            return False

        if not self.connected:
            Debug.error("Gerät nicht verbunden")
            return False

        if not self.is_gm_counter:
            Debug.error("Kein GM-Zähler verbunden")
            return False

        return True
