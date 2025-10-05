#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gyroscope GUI - Main entry point for the Gyroscope GUI application.
This module serves as the entry point when installed as a package.
"""

import sys
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
)
from .debug_utils import Debug
from .connection import ConnectionWindow
from .main_window import MainWindow
from .helper_classes import import_config

# Konfigurationsdatei laden
CONFIG = import_config()


def main():
    """
    Main entry point of the application.
    Initializes the debug system, starts the connection dialog,
    and creates the main window.
    """
    # Debug-System initialisieren
    match CONFIG["debug"]["level_default"]:
        case "verbose":
            debug_level = Debug.DEBUG_VERBOSE
        case "info":
            debug_level = Debug.DEBUG_INFO
        case "error":
            debug_level = Debug.DEBUG_ERROR
        case _:
            debug_level = Debug.DEBUG_OFF
    Debug.init(debug_level=debug_level, app_name=CONFIG["application"]["name"])

    # Globalen Exception-Handler registrieren
    sys.excepthook = Debug.exception_hook

    Debug.info("Starte Anwendung...")

    # QApplication erstellen
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    connection_dialog = ConnectionWindow(demo_mode=True, default_ip=CONFIG["connection"]["default_ip"])
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
