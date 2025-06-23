#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union
from PySide6.QtWidgets import QWidget  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QDialogButtonBox,
)
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


