#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime
import sys
import traceback
import inspect


class Debug:
    """
    Debug-Utility-Klasse für das Fringe Counter-Programm.

    Diese Klasse stellt zentrale Debug- und Logging-Funktionen bereit,
    um Fehler und Programmabläufe systematisch zu protokollieren.

    Attribute:
        logger: Der Logger für die Ausgabe von Debug-Informationen
        DEBUG_LEVEL: Das aktuell gesetzte Debug-Level (0-3)
        LOG_FILE: Pfad zur Log-Datei
    """

    # Debug-Level-Konstanten
    DEBUG_OFF = 0  # Keine Debug-Ausgabe
    DEBUG_ERROR = 1  # Nur Fehler werden angezeigt
    DEBUG_INFO = 2  # Fehler und wichtige Informationen werden angezeigt
    DEBUG_VERBOSE = 3  # Alle Informationen werden angezeigt

    # Standardwerte - Debug standardmäßig ausgeschaltet
    DEBUG_LEVEL = DEBUG_OFF
    LOG_FILE = None
    logger = None

    @classmethod
    def init(cls, debug_level=DEBUG_OFF, log_dir=None, app_name="fringe_counter"):
        """
        Initialisiert den Logger mit dem angegebenen Debug-Level und Log-Verzeichnis.

        Args:
            debug_level: Debug-Level (0-3)
            log_dir: Verzeichnis, in dem die Logs gespeichert werden sollen
            app_name: Name der Anwendung für die Log-Datei
        """
        cls.DEBUG_LEVEL = debug_level

        # Logger erstellen
        cls.logger = logging.getLogger(app_name)
        cls.logger.setLevel(logging.DEBUG)

        # Handler für Konsolenausgabe
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)

        # Debug-Level entsprechend setzen
        if debug_level >= cls.DEBUG_VERBOSE:
            console_handler.setLevel(logging.DEBUG)
        elif debug_level >= cls.DEBUG_INFO:
            console_handler.setLevel(logging.INFO)
        elif debug_level >= cls.DEBUG_ERROR:
            console_handler.setLevel(logging.ERROR)
        else:
            console_handler.setLevel(logging.CRITICAL)  # Praktisch nichts

        cls.logger.addHandler(console_handler)

        # Log-Datei einrichten
        # Wenn ein Verzeichnis angegeben wurde, wird es verwendet,
        # sonst einen "logs" Ordner im Projektverzeichnis
        if log_dir:
            log_directory = log_dir
        else:
            # Bestimme das Projektverzeichnis (ein Level über dem src-Verzeichnis)
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_directory = os.path.join(project_dir, "logs")

        if not os.path.exists(log_directory):
            try:
                os.makedirs(log_directory)
                print(f"Log-Verzeichnis erstellt: {log_directory}")
            except Exception as e:
                print(f"Fehler beim Erstellen des Log-Verzeichnisses: {e}")
                return

        # Immer eine log.txt im angegebenen Verzeichnis erstellen
        cls.LOG_FILE = os.path.join(
            log_directory,
            f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_fringecounter_log.txt",
        )

        file_handler = logging.FileHandler(cls.LOG_FILE, encoding="utf-8")
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # In Datei immer alles loggen
        cls.logger.addHandler(file_handler)

        cls.info(f"Log-Datei erstellt: {cls.LOG_FILE}")

    @classmethod
    def error(cls, message, exc_info=None):
        """
        Loggt eine Fehlermeldung.

        Args:
            message: Die zu loggende Fehlermeldung
            exc_info: Exception-Information (optional)
        """
        # Klassennamen und Funktionsnamen ermitteln
        if cls.DEBUG_LEVEL >= cls.DEBUG_VERBOSE:
            prefix = cls._get_caller_info()
            message = f"{prefix} {message}"

        if not cls.logger:
            print(f"FEHLER: {message}")
            return

        if exc_info:
            cls.logger.error(message, exc_info=True)
        else:
            cls.logger.error(message)

    @classmethod
    def info(cls, message):
        """
        Loggt eine Informationsmeldung.

        Args:
            message: Die zu loggende Information
        """
        # Klassennamen und Funktionsnamen ermitteln
        if cls.DEBUG_LEVEL >= cls.DEBUG_VERBOSE:
            prefix = cls._get_caller_info()
            message = f"{prefix} {message}"

        if not cls.logger:
            if cls.DEBUG_LEVEL >= cls.DEBUG_INFO:
                print(f"INFO: {message}")
            return

        cls.logger.info(message)

    @classmethod
    def debug(cls, message):
        """
        Loggt eine detaillierte Debug-Information.

        Args:
            message: Die zu loggende Debug-Information
        """
        # Klassennamen und Funktionsnamen ermitteln
        if cls.DEBUG_LEVEL >= cls.DEBUG_VERBOSE:
            prefix = cls._get_caller_info()
            message = f"{prefix} {message}"

        if not cls.logger:
            if cls.DEBUG_LEVEL >= cls.DEBUG_VERBOSE:
                print(f"DEBUG: {message}")
            return

        cls.logger.debug(message)

    @classmethod
    def critical(cls, message):
        """
        Loggt eine kritische Fehlermeldung.

        Args:
            message: Die zu loggende kritische Fehlermeldung
        """
        # Klassennamen und Funktionsnamen ermitteln
        if cls.DEBUG_LEVEL >= cls.DEBUG_VERBOSE:
            prefix = cls._get_caller_info()
            message = f"{prefix} {message}"

        if not cls.logger:
            print(f"KRITISCH: {message}")
            return

        cls.logger.critical(message)

    @classmethod
    def exception_hook(cls, exc_type, exc_value, exc_traceback):
        """
        Callback-Funktion für unbehandelte Ausnahmen.
        Protokolliert die Ausnahme und gibt sie an sys.__excepthook__ weiter.

        Args:
            exc_type: Der Typ der Ausnahme
            exc_value: Der Wert der Ausnahme
            exc_traceback: Der Traceback der Ausnahme
        """
        error_msg = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        cls.critical(f"Unbehandelte Ausnahme: {error_msg}")

        # Standardbehandlung von Ausnahmen
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    @classmethod
    def _get_caller_info(cls):
        """
        Ermittelt Informationen über den Aufrufer (Klasse und Funktion).

        Returns:
            str: Formatierte Information über den Aufrufer im Format [Klasse.Funktion]
        """
        # Inspiziere den Stack, um Aufruferinformationen zu erhalten
        stack = inspect.stack()

        # Position 0 ist diese Methode selbst
        # Position 1 ist die aufrufende Debug-Methode (debug, info, error, etc.)
        # Position 2 ist der tatsächliche Aufrufer, den wir identifizieren möchten
        if len(stack) > 2:
            caller = stack[2]
            frame = caller.frame

            # Versuche den Klassennamen zu ermitteln
            class_name = ""
            if "self" in frame.f_locals:
                instance = frame.f_locals["self"]
                class_name = instance.__class__.__name__

            # Hole den Funktionsnamen
            function_name = caller.function

            # Erzeuge die formatierte Aufruferinformation
            if class_name:
                return f"[{class_name}.{function_name}]"
            else:
                return f"[{function_name}]"

        return ""  # Fallback, falls Aufruferinformationen nicht ermittelt werden können
