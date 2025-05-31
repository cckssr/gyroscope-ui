#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Integrationstest für die refaktorierte HRNGGUI-Anwendung.
Überprüft die Grundfunktionalität der Anwendung nach der Umstrukturierung.
"""

import sys
import os
import time
from pathlib import Path
import unittest
import threading

# Sicherstellen, dass das Hauptverzeichnis im Python-Pfad ist
ROOT_DIR = Path(__file__).parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

from src.main_window import MainWindow
from src.connection import DeviceManager


class IntegrationTest(unittest.TestCase):
    """Integrationstest für die HRNGGUI-Anwendung."""

    @classmethod
    def setUpClass(cls):
        """Einmalige Einrichtung für alle Tests."""
        # Eine QApplication-Instanz wird für alle UI-Tests benötigt
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def setUp(self):
        """Testumgebung für jeden Test einrichten."""
        self.device_manager = DeviceManager()
        self.main_window = MainWindow(self.device_manager)

    def tearDown(self):
        """Aufräumen nach jedem Test."""
        if hasattr(self, "main_window"):
            self.main_window.close()

    def test_initialization(self):
        """Überprüft, ob das MainWindow korrekt initialisiert wird."""
        self.assertIsNotNone(self.main_window.ui)
        self.assertIsNotNone(self.main_window.data_controller)
        self.assertFalse(self.main_window.is_measuring)

    def test_ui_elements(self):
        """Überprüft, ob die UI-Elemente korrekt angelegt wurden."""
        # Plot
        self.assertIsNotNone(self.main_window.plot_widget)

        # Buttons
        self.assertTrue(hasattr(self.main_window.ui, "buttonStart"))
        self.assertTrue(hasattr(self.main_window.ui, "buttonStop"))
        self.assertTrue(hasattr(self.main_window.ui, "buttonSave"))
        self.assertTrue(hasattr(self.main_window.ui, "buttonReset"))

        # Anzeigen
        self.assertTrue(hasattr(self.main_window.ui, "cVoltage"))
        self.assertTrue(hasattr(self.main_window.ui, "cMode"))
        self.assertTrue(hasattr(self.main_window.ui, "cQueryMode"))
        self.assertTrue(hasattr(self.main_window.ui, "cDuration"))

    def test_reset_data(self):
        """Testet die Daten-Reset-Funktion."""
        # Mock für DataController erstellen
        original_reset = self.main_window.data_controller.reset
        reset_called = [False]

        def mock_reset():
            reset_called[0] = True
            original_reset()

        self.main_window.data_controller.reset = mock_reset

        # Reset aufrufen
        self.main_window.reset_data()

        # Überprüfen, ob reset aufgerufen wurde
        self.assertTrue(reset_called[0])

        # Ursprüngliche Methode wiederherstellen
        self.main_window.data_controller.reset = original_reset


def run_integration_tests():
    """Führt die Integrationstests aus."""
    test_suite = unittest.TestLoader().loadTestsFromTestCase(IntegrationTest)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(test_suite).wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
