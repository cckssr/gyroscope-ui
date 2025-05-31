#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HRNGGUI - Hauptprogramm für die Geiger-Müller Counter GUI-Anwendung.
"""

import sys
from PySide6.QtWidgets import QApplication, QMessageBox  # pylint: disable=import-error
from src.debug_utils import Debug
from src.config import APP_NAME, DEBUG_LEVEL_DEFAULT, MSG_CONNECTION_FAILED
from src.connection import ConnectionWindow
from src.main_window import MainWindow


def main():
    """
    Haupteinstiegspunkt der Anwendung.
    Initialisiert das Debug-System, startet die Verbindungsdialog
    und erstellt das Hauptfenster.
    """
    # Debug-System initialisieren
    debug_level = (
        Debug.DEBUG_VERBOSE if DEBUG_LEVEL_DEFAULT == "verbose" else Debug.DEBUG_OFF
    )
    Debug.init(debug_level=debug_level, app_name=APP_NAME)

    # Globalen Exception-Handler registrieren
    sys.excepthook = Debug.exception_hook

    Debug.info("Starte Anwendung...")

    # QApplication erstellen
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    # Verbindungsdialog anzeigen
    connection_dialog = ConnectionWindow()

    # Wenn der Dialog bestätigt wurde, Verbindung herstellen
    if connection_dialog.exec():
        success, device_manager = connection_dialog.attempt_connection()

        if success and device_manager is not None:
            # Hauptfenster erstellen und anzeigen, wenn Verbindung erfolgreich
            main_window = MainWindow(device_manager)
            main_window.show()

            # Timer starten, wenn vorhanden
            if hasattr(main_window, "timer"):
                main_window.timer.start()

            # Anwendung ausführen
            sys.exit(app.exec())
        else:
            # Fehlerfall: Verbindung fehlgeschlagen
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Icon.Critical)
            msgBox.setText(MSG_CONNECTION_FAILED)
            msgBox.setWindowTitle("Verbindungsfehler")
            msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)
            msgBox.exec()
            sys.exit(1)
    else:
        # Benutzer hat den Dialog abgebrochen
        Debug.info("Verbindung vom Benutzer abgebrochen")
        sys.exit(0)


if __name__ == "__main__":
    main()
