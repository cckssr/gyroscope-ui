#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import time
import socket
from tempfile import gettempdir
from typing import Union, Optional, Tuple
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QWidget,
    QApplication,
    QDialog,
    QDialogButtonBox,
)
from PySide6.QtCore import Slot, QTimer  # pylint: disable=no-name-in-module
from src.pyqt.ui_connection import Ui_Dialog as Ui_Connection
from src.debug_utils import Debug
from src.device_manager import DeviceManager
from src.helper_classes import import_config

CONFIG = import_config()["connection"]


class ConnectionWindow(QDialog):
    def __init__(
        self,
        parent: QWidget = None,
        demo_mode: bool = False,
        default_ip: str = "127.0.0.1:8080",
    ):
        """
        Initializes the connection window.
        Args:
            parent (QWidget, optional): Parent widget for the dialog. Defaults to None.
            demo_mode (bool, optional): If True, uses a mock port for demonstration purposes.
            default_ip (str, optional): The default IP address to connect to.
                Defaults to "127.0.0.1:8080".
        """
        # DeviceManager einmalig initialisieren (vermeidet doppelte Socket-Logik)
        self.device_manager = DeviceManager(status_callback=self.status_message)
        self.connection_successful = False
        self.ip = default_ip

        # Check if demo mode is active and mock arduino is available
        mock_arduino = self.check_mock_port()
        self.demo_mode = demo_mode and mock_arduino is not None
        Debug.debug(f"Demo mode is {'enabled' if self.demo_mode else 'disabled'}")
        if self.demo_mode:
            self.ip = mock_arduino[0] + ":" + mock_arduino[1]

        # Initialize parent and connection windows
        super().__init__(parent)
        self.ui = Ui_Connection()
        self.ui.setupUi(self)
        self._set_ssid_text(f"'{CONFIG['default_ssid']}'")

        # Attach functions to UI elements
        self.ui.buttonBox.accepted.connect(self.on_accept)
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Retry).clicked.connect(
            self.on_retry
        )

        # Setup auto-accept timer (2 seconds after successful connection)
        self.auto_accept_timer = QTimer(self)
        self.auto_accept_timer.setSingleShot(True)
        self.auto_accept_timer.timeout.connect(self._auto_accept)

        # Connect to device manager's connection successful signal
        self.device_manager.connection_successful.connect(
            self._on_connection_successful
        )

        # Attempt connection
        time.sleep(1)  # short delay to ensure connection is ready
        self._update_connection()

    def check_mock_port(self) -> Union[tuple[str, str], None]:
        """
        Checks if the mock virtual port is available.
        Returns:
            str: The mock port name if available, otherwise None.
        """
        filename = "mock_arduino_server_*.marker"
        matches = glob.glob(os.path.join(gettempdir(), filename))
        if matches:
            start = matches[0].find("server_")
            end = matches[0].find(".marker")
            ip = matches[0][start + len("server_") : end].split("_")
            host = ip[0]
            mock_port = ip[1]
            Debug.debug(f"Mock server found with IP {host}:{mock_port}")
            return host, mock_port
        return None

    def status_message(self, message, color="white"):
        """
        Updates the status message in the connection dialog.
        """
        self.ui.status_msg.setText(message)
        self.ui.status_msg.setStyleSheet(f"color: {color};")
        Debug.debug(f"Status message: {message}")
        QApplication.processEvents()  # Process events to update UI immediately
        self.ui.status_msg.repaint()  # Force repaint to ensure message is shown

    def _parse_host_port(self, ip: str) -> Tuple[str, int]:
        """Parse host:port from a string.

        Supports forms like 'host:port', 'http://host:port', '[ipv6]:port'.
        """
        ip = ip.strip()
        # Remove scheme
        if "://" in ip:
            ip = ip.split("://", 1)[1]
        # IPv6 wrapped in []
        if ip.startswith("["):
            host, rest = ip.split("]", 1)
            host = host[1:]
            if rest.startswith(":"):
                port = int(rest[1:])
            else:
                port = 80
            return host, port
        # Regular host:port
        if ip.count(":") == 1:
            host, port_s = ip.split(":", 1)
            try:
                port = int(port_s)
            except ValueError:
                port = 80
            return host, port
        # Host only
        return ip, 80

    def _set_ssid_text(self, ssid: str):
        """
        Set the SSID text in the UI.
        """
        prev_text = self.ui.desc.text()
        new_text = prev_text.replace("{ssid}", ssid)
        self.ui.desc.setText(new_text)

    def _update_connection(self):
        """
        Update the current connection status for UDP.

        Use DeviceManager directly to establish the real connection.
        """
        self.status_message("Verbinde über DeviceManager...", "yellow")

        # Verwende DeviceManager direkt für die Verbindung
        success = self.device_manager.connect_device(self.ip, 5.0)

        if success:
            self.connection_successful = True
            # Acquisition dauerhaft starten (Thread läuft unabhängig vom Mess-Flag)
            self.device_manager.start_acquisition()
            Debug.info(
                "UDP-Verbindung über DeviceManager erfolgreich, Datenerfassung gestartet"
            )
            self.status_message(
                "UDP-Verbindung erfolgreich hergestellt und getestet", "green"
            )
        else:
            self.connection_successful = False
            Debug.info("UDP-Verbindung über DeviceManager fehlgeschlagen")
            self.status_message(
                "UDP-Verbindung fehlgeschlagen - keine Daten empfangen", "red"
            )
        return success

    def closeEvent(self, event):  # noqa: N802 (Qt Namenskonvention)
        """Sicheres Beenden: Thread stoppen und Socket schließen.

        Verhindert Absturz beim Schließen des Dialogs durch laufenden QThread.
        """
        try:
            # Stop auto-accept timer if running
            if hasattr(self, "auto_accept_timer") and self.auto_accept_timer.isActive():
                self.auto_accept_timer.stop()
                Debug.debug("Auto-Accept Timer gestoppt")

            if hasattr(self, "device_manager") and self.device_manager:
                # Thread stoppen
                self.device_manager.stop_acquisition()
                # Verbindung schließen
                self.device_manager.disconnect_device()
        except Exception as e:  # pragma: no cover
            Debug.error(f"Fehler beim Schließen der Verbindung: {e}")
        super().closeEvent(event)

    @Slot()
    def on_accept(self):
        """Handle the accept button click."""
        # Stop auto-accept timer if running (user manually accepted)
        if hasattr(self, "auto_accept_timer") and self.auto_accept_timer.isActive():
            self.auto_accept_timer.stop()
            Debug.debug("Auto-Accept Timer gestoppt (manuelle Akzeptierung)")

        if self.connection_successful:
            self.accept()
        else:
            self.status_message("Connection failed", "red")

    @Slot()
    def on_retry(self):
        """Handle the retry button click for UDP connection."""
        self.status_message("Teste UDP-Verbindung erneut...", "yellow")
        # Stoppe vorherige Verbindung falls vorhanden
        if hasattr(self, "device_manager") and self.device_manager:
            self.device_manager.stop_acquisition()
            self.device_manager.disconnect_device()
        # Versuche erneut zu verbinden
        self._update_connection()

    @Slot()
    def _on_connection_successful(self):
        """Handle successful connection signal from device manager."""
        Debug.info(
            "Verbindung erfolgreich und getestet, starte Auto-Accept Timer (2 Sekunden)"
        )
        self.status_message(
            "Verbindung erfolgreich getestet! Auto-Accept in 2 Sekunden...", "green"
        )
        self.auto_accept_timer.start(2000)  # 2 seconds

    @Slot()
    def _auto_accept(self):
        """Automatically accept the connection after timer expires."""
        if self.connection_successful:
            Debug.info("Auto-Accept: Verbindung wird automatisch akzeptiert")
            self.status_message("Verbindung automatisch akzeptiert", "green")
            self.accept()
        else:
            Debug.debug(
                "Auto-Accept Timer abgelaufen, aber Verbindung nicht erfolgreich"
            )
