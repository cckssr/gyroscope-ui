#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Union
from PySide6.QtWidgets import QWidget  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QWidget,
    QApplication,
    QDialog,
    QDialogButtonBox,
)
from tempfile import gettempdir
from serial.tools import list_ports
from pyqt.ui_connection import Ui_Dialog as Ui_Connection
from src.helper_classes import AlertWindow
from src.debug_utils import Debug
from src.device_manager import DeviceManager


class ConnectionWindow(QDialog):
    def __init__(
        self,
        parent: QWidget = None,
        demo_mode: bool = False,
        default_device: str = "None",
    ):
        """
        Initializes the connection window.

        Args:
            parent (QWidget, optional): Parent widget for the dialog. Defaults to None.
            demo_mode (bool, optional): If True, uses a mock port for demonstration purposes.
            default_device (str, optional): The default device to connect to. Defaults to "None".
        """
        self.device_manager = DeviceManager(status_callback=self.status_message)
        self.connection_successful = False
        self.default_device = default_device
        self.ports = []  # List to hold available ports

        # Check if demo mode is active and mock port is available
        mock_port = self.check_mock_port()
        self.demo_mode = demo_mode and mock_port is not None
        Debug.debug(f"Demo mode is {'enabled' if self.demo_mode else 'disabled'}")
        if self.demo_mode:
            self.ports.append(
                [mock_port, "Mock Device", "Virtual device for demonstration purposes"]
            )

        # Initialize parent and connection windows
        super().__init__(parent)
        self.ui = Ui_Connection()
        self.ui.setupUi(self)
        self.combo = self.ui.comboSerial  # Use the combo box from the UI
        self._update_ports()  # Initialize available ports

        # Attach functions to UI elements
        self.ui.buttonRefreshSerial.clicked.connect(self._update_ports)
        self.combo.currentIndexChanged.connect(self._update_port_description)

    def check_mock_port(self) -> Union[str, None]:
        """
        Checks if the mock virtual port is available.
        Returns:
            str: The mock port name if available, otherwise None.
        """
        path = os.path.join(gettempdir(), "virtual_serial_port.txt")
        Debug.debug(f"Checking for mock port at: {path}")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                port = f.read().strip()
                Debug.debug(f"Mock port found: {port}")
                return port
        return None

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
        if self.demo_mode:
            self.ports = self.ports[:1]  # Clear all but the mock port
        else:
            self.ports = []

        Debug.info(f"Resetting available ports to {self.ports}")

        # Get available ports
        ports = list_ports.comports()
        arduino_index = -1  # Index if the default device is found

        for i, port in enumerate(ports):
            Debug.debug(f"Found port: {port.device} - {port.description}")
            self.ports.append(
                [port.device, port.name, port.description]
            )  # Store port object for later use
            # Check if the port matches the default device
            if self.default_device in port.description and arduino_index == -1:
                arduino_index = i + int(self.demo_mode)

        Debug.debug(f"Available ports updated: {self.ports}")
        # Add ports to the combo box
        for port in self.ports:
            self.combo.addItem(port[0], port[2])

        # Setze Arduino-Port als vorausgewählt, wenn gefunden
        if arduino_index != -1:
            self.combo.setCurrentIndex(arduino_index)
            self._update_port_description()

    def _update_port_description(self):
        """
        Updates the port description based on the selected port.
        """
        index = self.combo.currentIndex()
        if index >= 0:
            port = self.ports[index]
            device = port[1]
            description = port[2]
            address = port[0]
        # If no valid index, clear the fields
        else:
            device = ""
            address = ""
            description = ""

        self.ui.device_name.setText(device)
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
        self.status_message(f"Connecting to {port}...", "white")
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

            # Show error dialog with retry options
            error_msg = f"Failed to connect to {self.combo.currentText()}"
            alert = AlertWindow(
                self,
                message=f"{error_msg}\n\nPlease check if the device is connected properly and try again.",
                title="Connection Error",
                buttons=[
                    ("Retry", QDialogButtonBox.ButtonRole.ResetRole),
                    ("Select Another Port", QDialogButtonBox.ButtonRole.ActionRole),
                    ("Cancel", QDialogButtonBox.ButtonRole.RejectRole),
                ],
            )

            # Dialog anzeigen und auf Benutzeraktion warten
            result = alert.exec()

            # Benutzerentscheidung verarbeiten
            role = alert.get_clicked_role()

            if (
                role == QDialogButtonBox.ButtonRole.RejectRole
                or result == QDialog.Rejected
            ):
                # Benutzer hat "Abbrechen" gewählt oder Dialog abgebrochen
                Debug.info("User canceled connection attempt")
                return super().reject()

            elif role == QDialogButtonBox.ButtonRole.ActionRole:
                # Benutzer möchte einen anderen Port auswählen
                Debug.info("User chose to select another port")
                return False  # Dialog offen lassen

            elif role == QDialogButtonBox.ButtonRole.ResetRole:
                # Erneut mit demselben Port versuchen
                Debug.info(f"Retrying connection with port: {self.combo.currentText()}")
                return self.accept()  # Rekursiver Aufruf

            # Fallback, wenn kein Button erfasst wurde
            return False
