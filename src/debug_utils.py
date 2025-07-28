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
    Debug utility class for the Fringe Counter program.

    This class provides central debug and logging functions,
    to systematically log errors and program flow.

    Attribute:
        logger: The logger used for debug output
        DEBUG_LEVEL: Current debug level (0-3)
        LOG_FILE: Path to the log file
    """

    # Debug level constants
    DEBUG_OFF = 0  # No debug output
    DEBUG_ERROR = 1  # Only errors are shown
    DEBUG_INFO = 2  # Errors and important information are shown
    DEBUG_VERBOSE = 3  # All information is shown

    # Default values - debugging disabled by default
    DEBUG_LEVEL = DEBUG_OFF
    LOG_FILE = None
    logger = None

    @classmethod
    def init(cls, debug_level=DEBUG_OFF, log_dir=None, app_name="fringe_counter"):
        """
        Initialisiert den Logger mit dem angegebenen Debug-Level und Log-Verzeichnis.

        Args:
            debug_level: Debug level (0-3)
            log_dir: Directory where logs should be stored
            app_name: Application name used for the log file
        """
        cls.DEBUG_LEVEL = debug_level

        # Create logger
        cls.logger = logging.getLogger(app_name)
        cls.logger.setLevel(logging.DEBUG)

        # Handler for console output
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)

        # Set debug level accordingly
        if debug_level >= cls.DEBUG_VERBOSE:
            console_handler.setLevel(logging.DEBUG)
        elif debug_level >= cls.DEBUG_INFO:
            console_handler.setLevel(logging.INFO)
        elif debug_level >= cls.DEBUG_ERROR:
            console_handler.setLevel(logging.ERROR)
        else:
            console_handler.setLevel(logging.CRITICAL)  # Praktisch nichts

        cls.logger.addHandler(console_handler)

        # Set up log file
         # Use provided directory if given,
        # otherwise use a "logs" folder in the project directory
        if log_dir:
            log_directory = log_dir
        else:
            # Determine the project directory (one level above the src directory)
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_directory = os.path.join(project_dir, "logs")

        if not os.path.exists(log_directory):
            try:
                os.makedirs(log_directory)
                print(f"Log directory created: {log_directory}")
            except Exception as e:
                print(f"Error creating log directory: {e}")
                return

        # Always create a log.txt in the specified directory
        cls.LOG_FILE = os.path.join(
            log_directory,
            f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_fringecounter_log.txt",
        )

        file_handler = logging.FileHandler(cls.LOG_FILE, encoding="utf-8")
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # In Datei immer alles loggen
        cls.logger.addHandler(file_handler)

        cls.info(f"Log file created: {cls.LOG_FILE}")

    @classmethod
    def error(cls, message, exc_info=None):
        """
        Log an error message.

        Args:
            message: Error message to log
            exc_info: Exception info (optional)
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
        Log an informational message.

        Args:
            message: Information to log
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
        Log detailed debug information.

        Args:
            message: Debug information to log
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
        Log a critical error message.

        Args:
            message: Critical error message to log
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
        Callback function for unhandled exceptions.
        Logs the exception and forwards it to sys.__excepthook__.

        Args:
            exc_type: The exception type
            exc_value: The exception value
            exc_traceback: The traceback
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
        Retrieve information about the caller (class and function).

        Returns:
            str: Formatted information about the caller in the format [Class.Function]
        """
        # Inspiziere den Stack, um Aufruferinformationen zu erhalten
        stack = inspect.stack()

        # Position 0 is this method
        # Position 1 is the calling debug method (debug, info, error, etc.)
        # Position 2 is the actual caller we want to identify
        if len(stack) > 2:
            caller = stack[2]
            frame = caller.frame

            # Try to determine the class name
            class_name = ""
            if "self" in frame.f_locals:
                instance = frame.f_locals["self"]
                class_name = instance.__class__.__name__

            # Get the function name
            function_name = caller.function

            # Create the formatted caller information
            if class_name:
                return f"[{class_name}.{function_name}]"
            else:
                return f"[{function_name}]"

        return ""  # Fallback if caller information cannot be determined
