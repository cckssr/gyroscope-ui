#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HRNGGUI - Hauptprogramm für die Geiger-Müller Counter GUI-Anwendung.
"""

import sys
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
)
from src.debug_utils import Debug
from src.connection import ConnectionWindow
from src.main_window import MainWindow
from src.helper_classes import import_config

# Konfigurationsdatei laden
CONFIG = import_config()


def main():
    """
    Haupteinstiegspunkt der Anwendung.
    Initialisiert das Debug-System, startet die Verbindungsdialog
    und erstellt das Hauptfenster.
    """
    # Debug-System initialisieren
    debug_level = (
        Debug.DEBUG_VERBOSE
        if CONFIG["debug"]["level_default"] == "verbose"
        else Debug.DEBUG_OFF
    )
    Debug.init(debug_level=debug_level, app_name=CONFIG["application"]["name"])

    # Globalen Exception-Handler registrieren
    sys.excepthook = Debug.exception_hook

    Debug.info("Starte Anwendung...")

    # QApplication erstellen
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    connection_dialog = ConnectionWindow(demo_mode=True)
    if connection_dialog.exec():
        success = connection_dialog.connection_successful
        device_manager = connection_dialog.device_manager
        if success and device_manager is not None and device_manager.connected:
            # Hauptfenster erstellen
            main_window = MainWindow(device_manager)
            main_window.show()
            # Event Loop starten
            exit_code = app.exec()
            # Sauber herunterfahren
            try:
                device_manager.shutdown()
            except Exception:  # pragma: no cover
                pass
            sys.exit(exit_code)
        else:
            # Verbindung fehlgeschlagen
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setText(CONFIG["messages"]["connection_failed"])
            msg_box.setWindowTitle("Verbindungsfehler")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
            # DeviceManager dennoch schließen
            try:
                device_manager.shutdown()
            except Exception:  # pragma: no cover
                pass
            sys.exit(1)
    else:
        # Benutzer hat Dialog abgebrochen -> DeviceManager ggf. schließen
        try:
            dm = getattr(connection_dialog, "device_manager", None)
            if dm:
                dm.shutdown()
        except Exception:  # pragma: no cover
            pass
        Debug.info("Verbindung vom Benutzer abgebrochen")
        sys.exit(0)


if __name__ == "__main__":
    main()
