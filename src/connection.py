#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import time
import math
from typing import Union
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
        Verbindet mit dem angegebenen Geräteport und startet automatisch die Datenerfassung.
        Verbesserte Implementierung mit detaillierten Diagnosen und automatischem Thread-Start.

        Args:
            port (str): Der Port, mit dem verbunden werden soll

        Returns:
            bool: True wenn die Verbindung erfolgreich war, False sonst
        """
        self.port = port
        Debug.info(f"DeviceManager: Versuche Verbindung mit Gerät an Port: {port}")

        # Zuerst sicherstellen, dass keine aktive Datenerfassung läuft
        self.stop_acquisition()

        # Existierende Verbindungen zuerst schließen
        if hasattr(self, "device") and self.device:
            try:
                Debug.info("Schließe eventuell vorhandene Verbindung")
                self.device.close()
            except Exception as e:
                Debug.error(f"Fehler beim Schließen der vorherigen Verbindung: {e}")

        # Mock-Modus für Demonstrationszwecke
        if port == "/dev/ttymock":
            Debug.info(f"Verwende Mock-Gerät an Port: {port}")
            if self.status_callback:
                self.status_callback(f"Verbunden mit Mock-Gerät: {port}", "orange")
            self.connected = True
            self.is_gm_counter = False

            # Automatisch Datenerfassung starten
            self.start_acquisition()
            return True

        try:
            # Informiere über den Verbindungsversuch
            Debug.info(f"Versuche, mit GM-Zähler am Port {port} zu verbinden...")
            if self.status_callback:
                self.status_callback(f"Verbinde mit GM-Zähler an {port}...", "blue")

            # GM-Counter ist obligatorisch, kein Fallback mehr auf einfachen Arduino
            self.device = GMCounter(port=port)
            self.is_gm_counter = True

            # Prüfe, ob die Verbindung erfolgreich war
            if self.device and self.device.connected:
                self.connected = True
                Debug.info(f"Erfolgreich mit GM-Zähler an Port {port} verbunden")

                # Hole Geräteinformationen für bessere Diagnose
                try:
                    device_info = self.device.get_information()
                    Debug.info(
                        f"GM-Zähler Version: {device_info.get('version', 'unbekannt')}"
                    )
                    Debug.info(
                        f"GM-Zähler Copyright: {device_info.get('copyright', 'unbekannt')}"
                    )

                    if self.status_callback:
                        version_text = device_info.get("version", "unbekannt")
                        self.status_callback(
                            f"GM-Zähler verbunden an {port} (Version: {version_text})",
                            "green",
                        )

                except Exception as e:
                    Debug.error(
                        f"Warnung: Geräteinformationen konnten nicht abgerufen werden: {e}"
                    )
                    if self.status_callback:
                        self.status_callback(f"GM-Zähler verbunden an {port}", "green")

                # Automatisch Datenerfassung starten
                self.start_acquisition()
                return True
            else:
                Debug.error(f"GM-Zähler an {port} konnte nicht initialisiert werden")
                self.connected = False
                self.is_gm_counter = False
                if self.status_callback:
                    self.status_callback(
                        f"Konnte GM-Zähler an {port} nicht initialisieren", "red"
                    )
                return False

        except Exception as e:
            Debug.error(
                f"Fehler beim Verbinden mit Gerät an {port}: {e}", exc_info=True
            )
            self.connected = False
            self.is_gm_counter = False

            # Gib zusätzliche Informationen zum Fehler
            error_message = str(e)
            if "Permission denied" in error_message:
                error_hint = f"Fehlende Zugriffsrechte für {port}. Überprüfen Sie die Berechtigungen."
            elif "Device or resource busy" in error_message:
                error_hint = (
                    f"Port {port} wird bereits von einem anderen Programm verwendet."
                )
            elif "No such file or directory" in error_message:
                error_hint = f"Port {port} existiert nicht oder ist nicht verfügbar."
            else:
                error_hint = error_message

            if self.status_callback:
                self.status_callback(f"Verbindungsfehler: {error_hint}", "red")

            return False

    def start_acquisition(self):
        """
        Startet den Datenerfassungs-Thread.
        Verbesserte Implementierung mit mehr Sicherheitsprüfungen und Status-Updates.

        Returns:
            bool: True wenn die Datenerfassung gestartet wurde, False bei Fehlern
        """
        # Sicherheitsprüfung: Ist das Gerät verbunden?
        if not self.is_connected():
            Debug.error("Cannot start acquisition: device not connected")
            if self.status_callback:
                self.status_callback(
                    "Datenerfassung nicht möglich: Gerät nicht verbunden", "red"
                )
            return False

        # Sicherheitsprüfung: Läuft bereits ein Thread?
        if self.running and self.acquire_thread and self.acquire_thread.is_alive():
            Debug.info("Data acquisition already running")
            return True  # Bereits aktiv, kein Problem

        Debug.info("Starting data acquisition")
        self.stop_event.clear()  # Event zurücksetzen
        self.running = True

        # Thread erstellen und starten
        self.acquire_thread = Thread(
            target=self._acquisition_loop, name="DataAcquisition"
        )
        self.acquire_thread.daemon = True  # Als Daemon-Thread markieren
        self.acquire_thread.start()

        # Erfolgsstatus zurückmelden
        Debug.debug(f"Acquisition thread started: {self.acquire_thread.name}")
        if self.status_callback:
            self.status_callback("Datenerfassung gestartet", "green")
        return True

    def stop_acquisition(self):
        """
        Stoppt den Datenerfassungs-Thread sauber.
        Verbesserte Implementierung mit besserer Thread-Beendigung und Status-Feedback.

        Returns:
            bool: True wenn die Datenerfassung erfolgreich gestoppt wurde
        """
        # Wenn kein Thread läuft oder running bereits False, nichts tun
        if (
            not self.running
            or not self.acquire_thread
            or not self.acquire_thread.is_alive()
        ):
            Debug.info("No acquisition running, nothing to stop")
            return True

        Debug.info("Stopping data acquisition")
        self.running = False
        self.stop_event.set()  # Event setzen, um Thread zu benachrichtigen

        # Auf das Ende des Threads warten, mit Timeout
        if self.acquire_thread and self.acquire_thread.is_alive():
            Debug.debug(
                f"Waiting for acquisition thread to terminate: {self.acquire_thread.name}"
            )

            # Warten mit höherem Timeout für saubereres Beenden
            self.acquire_thread.join(timeout=2.0)

            # Prüfen, ob der Thread tatsächlich beendet wurde
            if self.acquire_thread.is_alive():
                Debug.info(
                    f"Acquisition thread did not terminate within timeout: {self.acquire_thread.name}"
                )
                if self.status_callback:
                    self.status_callback(
                        "Datenerfassung wurde nicht sauber beendet", "orange"
                    )
                return False

        # Thread erfolgreich beendet
        if self.status_callback:
            self.status_callback("Datenerfassung gestoppt", "blue")
        return True

    def _generate_mock_data(self, index: int) -> tuple:
        """
        Generiert Mock-Daten für den Demo-Modus mit realistischen Zufallswerten.
        Implementiert verschiedene Verteilungsmuster für ein realistischeres Demoverhalten.

        Args:
            index: Der aktuelle Index für die Callback-Funktion

        Returns:
            tuple: (neuer_index, Wartezeit) - Der inkrementierte Index und die simulierte Wartezeit
        """
        # Verschiedene Simulationsmodi für unterschiedliche Verhaltensweisen
        simulation_mode = index % 300  # Ändert das Verhalten alle 300 Datenpunkte

        if simulation_mode < 100:
            # Normaler Zufallsbereich
            base_value = random.randint(50, 150)
            value = base_value * 10  # Werte im Bereich 500-1500 μs
        elif simulation_mode < 200:
            # Sinusförmiges Muster mit Rauschen
            base_value = 100 + 50 * math.sin(index / 20)
            noise = random.randint(-20, 20)
            value = int((base_value + noise) * 10)
        else:
            # Gelegentliche Ausreißer
            if random.random() < 0.05:  # 5% Chance für Ausreißer
                value = random.randint(2000, 3000)
            else:
                value = random.randint(500, 1500)

        # Sicherstellen, dass der Wert im gültigen Bereich liegt
        value = max(50, min(3000, value))

        Debug.debug(f"Generated mock value: {value} μs")

        if self.data_callback:
            self.data_callback(index, value)

        # Simulation der Verarbeitungszeit mit realistischerer Verzögerung
        wait_time = max(0.05, (value / 10000) + random.uniform(0.01, 0.1))
        return index + 1, wait_time

    def _convert_value_if_needed(
        self, value: Union[int, float, str, None]
    ) -> Union[int, float, str, None]:
        """
        Konvertiert Zeichenketten in Zahlen, wenn nötig.
        Verbesserte Implementierung mit zusätzlicher Validierung.

        Args:
            value: Der zu konvertierende Wert

        Returns:
            Union[int, float, str, None]: Der konvertierte Wert oder der ursprüngliche Wert
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return value  # Bereits ein numerischer Wert, keine Konvertierung notwendig

        if isinstance(value, str):
            # Entferne Leerzeichen und ersetze Kommas durch Punkte (für deutsche Zahlenformate)
            cleaned_value = value.strip().replace(",", ".")

            try:
                # Versuche zuerst, als Integer zu konvertieren
                if "." not in cleaned_value:
                    converted = int(cleaned_value)
                else:
                    # Andernfalls als Float konvertieren
                    converted = float(cleaned_value)

                Debug.debug(
                    f"Konvertiert '{value}' zu {type(converted).__name__}: {converted}"
                )
                return converted
            except (ValueError, TypeError) as e:
                Debug.error(
                    f"Konnte Wert '{value}' nicht in eine Zahl konvertieren: {e}"
                )

        return value  # Rückgabe des Originalwerts, wenn keine Konvertierung möglich ist

    def _acquisition_loop(self):
        """
        Main acquisition loop that runs in a separate thread.
        For mock device, generates random data.
        For real device, reads from Arduino.

        Implementiert ein robustes Fehlerbehandlungs- und Backoff-System,
        um eine zuverlässige Datenerfassung zu gewährleisten.

        Die Schleife läuft kontinuierlich im Hintergrund und versucht automatisch,
        die Verbindung wiederherzustellen, wenn Probleme auftreten.
        """
        k = 0
        consecutive_errors = 0
        reconnect_attempts = 0
        backoff_time = 0.1  # Initial backoff time in seconds
        max_backoff_time = 5.0  # Maximum backoff time
        Debug.info("Starting data acquisition loop")

        while self.running and not self.stop_event.is_set():
            try:
                # Mock-Modus
                if self.port == "/dev/ttymock":
                    k, wait_time = self._generate_mock_data(k)
                    time.sleep(wait_time)
                    # Reset error counter in successful mock operation
                    consecutive_errors = 0
                    reconnect_attempts = 0
                    backoff_time = 0.1
                    continue

                # Prüfen der Verbindung zum Gerät mit automatischer Wiederverbindung
                if not self.monitor_connection(attempt_reconnect=True):
                    Debug.info("Gerät nicht verbunden. Warte und prüfe erneut.")
                    time.sleep(backoff_time)

                    # Nach mehreren Fehlern Auto-Reconnect versuchen
                    reconnect_attempts += 1
                    if reconnect_attempts >= 3 and reconnect_attempts % 3 == 0:
                        if self.auto_reconnect():
                            reconnect_attempts = 0
                            consecutive_errors = 0
                            backoff_time = 0.1
                    continue

                # Bei erfolgreicher Verbindung Reset der Reconnect-Versuche
                reconnect_attempts = 0

                # Lesen vom GM-Counter
                data = self.device.get_data(False)

                if data is None or not isinstance(data, dict):
                    Debug.debug("Keine gültigen Daten empfangen, versuche erneut.")
                    time.sleep(0.5)
                    continue

                # Extrahiere den Count-Wert aus dem Dictionary
                value = data.get("count")

                # Callback nur wenn gültiger Wert
                if value is not None and self.data_callback:
                    self.data_callback(k, value)
                    k += 1
                    # Reset bei erfolgreicher Datenabfrage
                    consecutive_errors = 0
                    backoff_time = 0.1

            except Exception as e:
                consecutive_errors += 1
                # Exponentielles Backoff bei wiederholten Fehlern
                backoff_time = min(max_backoff_time, backoff_time * 1.5)

                error_msg = f"Fehler in Datenerfassungsschleife: {e}"

                # Detailliertes Logging nur bei nicht zu häufigen Fehlern
                if consecutive_errors < 5 or consecutive_errors % 10 == 0:
                    Debug.error(error_msg, exc_info=True)
                    if self.status_callback:
                        self.status_callback(f"Messfehler: {e}", "red")
                else:
                    Debug.debug(
                        f"{error_msg} (wiederholter Fehler {consecutive_errors})"
                    )

                # Warten mit exponentieller Backoff-Zeit
                time.sleep(backoff_time)

                # Überprüfen, ob die Schleife fortgesetzt werden soll
                if consecutive_errors > 100:
                    Debug.critical(
                        "Zu viele Fehler in der Datenerfassungsschleife, Erfassung wird angehalten."
                    )
                    self.running = False
                    if self.status_callback:
                        self.status_callback(
                            "Datenerfassung wegen zu vieler Fehler gestoppt", "red"
                        )
                    break

        Debug.info("Acquisition loop terminated")

    def is_connected(self) -> bool:
        """
        Prüft die Verbindung zum Gerät mit detaillierten Diagnostikinformationen.

        Returns:
            bool: True, wenn das Gerät verbunden ist, False sonst

        Notes:
            Bei False gibt die Methode automatisch eine entsprechende Fehlermeldung aus.
        """
        # Mock-Geräte sind immer verbunden
        if self.port == "/dev/ttymock":
            return self.connected

        # Prüfschritte für reale Geräte
        if not self.device:
            Debug.error("Kein Gerät vorhanden")
            return False

        if not self.connected:
            Debug.error("Gerät nicht verbunden")
            return False

        if not self.is_gm_counter:
            Debug.error("Kein GM-Zähler verbunden")
            return False

        # Optional: Bei echtem Gerät kann hier eine aktive Verbindungsprüfung stattfinden
        if hasattr(self.device, "serial") and self.device.serial:
            try:
                # Prüfen, ob die serielle Verbindung noch aktiv ist
                if not self.device.serial.is_open:
                    Debug.error("Serielle Verbindung wurde getrennt")
                    self.connected = False
                    return False
            except Exception as e:
                Debug.error(f"Fehler bei der Verbindungsprüfung: {e}")
                self.connected = False
                return False

        return True

    def monitor_connection(self, attempt_reconnect=True) -> bool:
        """
        Überwacht die Verbindung zum Gerät und versucht bei Bedarf eine Wiederherstellung.
        Diese Methode wird vom Acquisition Thread aufgerufen, um die Verbindungsstabilität zu gewährleisten.

        Args:
            attempt_reconnect (bool): Ob bei unterbrochener Verbindung eine Wiederverbindung versucht werden soll

        Returns:
            bool: True wenn die Verbindung aktiv ist oder wiederhergestellt wurde, sonst False
        """
        # Mock-Geräte benötigen keine Überwachung
        if self.port == "/dev/ttymock":
            return True

        # Wenn kein Gerät existiert, können wir nichts tun
        if not hasattr(self, "device") or not self.device:
            Debug.error("Kein Gerät für Verbindungsüberwachung vorhanden")
            return False

        try:
            # Verbindung prüfen
            if not self.is_connected():
                Debug.info("Gerät nicht verbunden bei Verbindungsüberwachung")

                # Wenn Wiederverbindung nicht gewünscht, hier abbrechen
                if not attempt_reconnect:
                    return False

                # Wiederverbindung versuchen
                Debug.info("Versuche Wiederverbindung zum Gerät...")
                if hasattr(self.device, "reconnect"):
                    try:
                        # Status-Update vor dem Verbindungsversuch
                        if self.status_callback:
                            self.status_callback(
                                "Verbindung wird wiederhergestellt...", "blue"
                            )

                        reconnect_success = self.device.reconnect()
                        self.connected = reconnect_success

                        if reconnect_success:
                            Debug.info(
                                "Wiederverbindung zum Gerät erfolgreich hergestellt"
                            )
                            if self.status_callback:
                                self.status_callback(
                                    f"Verbindung wiederhergestellt zu {self.port}",
                                    "green",
                                )
                            return True
                        else:
                            Debug.error("Wiederverbindung zum Gerät fehlgeschlagen")
                            if self.status_callback:
                                self.status_callback(
                                    "Verbindung konnte nicht wiederhergestellt werden",
                                    "red",
                                )
                            return False
                    except Exception as reconnect_error:
                        Debug.error(
                            f"Fehler bei Wiederverbindungsversuch: {reconnect_error}",
                            exc_info=True,
                        )
                        if self.status_callback:
                            self.status_callback(
                                f"Wiederverbindungsfehler: {reconnect_error}", "red"
                            )
                        return False
                else:
                    Debug.error("Gerät unterstützt keine Wiederverbindung")
                    return False

            # Aktiven seriellen Port überprüfen
            if hasattr(self.device, "serial") and self.device.serial:
                try:
                    if not self.device.serial.is_open:
                        Debug.info(
                            "Serielle Verbindung ist geschlossen, versuche neu zu öffnen"
                        )
                        self.device.serial.open()
                        if self.device.serial.is_open:
                            Debug.info(
                                "Serielle Verbindung erfolgreich wieder geöffnet"
                            )
                            return True
                        else:
                            Debug.error(
                                "Konnte serielle Verbindung nicht wieder öffnen"
                            )
                            return False
                except Exception as serial_error:
                    Debug.error(
                        f"Fehler bei Überprüfung/Öffnung des seriellen Ports: {serial_error}"
                    )
                    return False

            return True  # Verbindung ist intakt

        except Exception as e:
            Debug.error(f"Fehler bei der Verbindungsüberwachung: {e}", exc_info=True)
            self.connected = False
            return False

    def auto_reconnect(self):
        """
        Versucht automatisch, die Verbindung wiederherzustellen, wenn sie unterbrochen wurde.
        Diese Methode kann vom Acquisition Thread aufgerufen werden, wenn Verbindungsprobleme erkannt werden.

        Returns:
            bool: True wenn die Wiederverbindung erfolgreich war, False sonst
        """
        if self.port == "None" or self.port == "/dev/ttymock":
            return False

        Debug.info(f"Automatische Wiederverbindung mit {self.port} wird versucht...")
        if self.status_callback:
            self.status_callback(f"Versuche Verbindung wiederherzustellen...", "blue")

        # Stop any running acquisition
        self.stop_acquisition()

        # Attempt to close any existing connection
        if hasattr(self, "device") and self.device:
            try:
                self.device.close()
            except Exception as e:
                Debug.error(f"Fehler beim Schließen der Verbindung für Reconnect: {e}")

        # Try to reconnect
        try:
            self.device = GMCounter(port=self.port)
            self.is_gm_counter = True

            if self.device and self.device.connected:
                self.connected = True
                Debug.info(f"Wiederverbindung mit {self.port} erfolgreich")

                if self.status_callback:
                    self.status_callback(f"Verbindung wiederhergestellt", "green")

                # Restart acquisition
                self.start_acquisition()
                return True
            else:
                Debug.error(
                    f"Wiederverbindung fehlgeschlagen: Gerät konnte nicht initialisiert werden"
                )
                self.connected = False
                return False

        except Exception as e:
            Debug.error(
                f"Fehler bei automatischer Wiederverbindung: {e}", exc_info=True
            )
            self.connected = False

            if self.status_callback:
                self.status_callback(f"Wiederverbindung fehlgeschlagen", "red")

            return False
