#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unit-Tests für die MainWindow-Klasse.
"""

import sys
from pathlib import Path
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

pytest.importorskip("PySide6.QtWidgets")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from src.main_window import MainWindow
from src.data_controller import DataController


class TestMainWindow(unittest.TestCase):
    """Testfälle für die MainWindow-Klasse."""

    @classmethod
    def setUpClass(cls):
        """Einmalige Einrichtung für alle Tests."""
        # Eine QApplication-Instanz wird für alle UI-Tests benötigt
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def setUp(self):
        """Testumgebung für jeden Test einrichten."""
        # Mock für Arduino-Verbindungen und andere externe Abhängigkeiten
        self.arduino_patcher = patch("src.main_window.Arduino")
        self.gm_counter_patcher = patch("src.main_window.GMCounter")
        self.debug_patcher = patch("src.main_window.Debug")

        self.mock_arduino = self.arduino_patcher.start()
        self.mock_gm_counter = self.gm_counter_patcher.start()
        self.mock_debug = self.debug_patcher.start()

        # MainWindow-Instanz erstellen
        self.main_window = MainWindow()

        # DataController-Mock erstellen
        self.main_window.data_controller = Mock(spec=DataController)

    def tearDown(self):
        """Aufräumen nach jedem Test."""
        # Alle Patches beenden
        self.arduino_patcher.stop()
        self.gm_counter_patcher.stop()
        self.debug_patcher.stop()

        # Alle Timer stoppen
        if hasattr(self.main_window, "count_timer"):
            self.main_window.count_timer.stop()
        if hasattr(self.main_window, "plot_timer"):
            self.main_window.plot_timer.stop()

        # MainWindow schließen
        self.main_window.close()

    def test_init(self):
        """Testet, ob das MainWindow korrekt initialisiert wird."""
        self.assertIsNotNone(self.main_window.ui)
        self.assertIsNotNone(self.main_window.data_controller)
        self.assertFalse(self.main_window.counting)

    @patch("src.main_window.QFileDialog.getSaveFileName")
    def test_save_csv(self, mock_file_dialog):
        """Testet die Speicherfunktion für CSV-Dateien."""
        # Temporäre Datei erstellen
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
            temp_path = temp_file.name

        # Den Mock so konfigurieren, dass er den Pfad zur temporären Datei zurückgibt
        mock_file_dialog.return_value = (temp_path, "CSV (*.csv)")

        # DataController-Mock so konfigurieren, dass er Testdaten zurückgibt
        self.main_window.data_controller.get_csv_data.return_value = [
            ["Messung", "Anzahl"],
            ["Messung 1", "100"],
            ["Messung 2", "200"],
        ]

        # Funktion aufrufen
        self.main_window.save_csv()

        # Überprüfen, ob der FileDialog aufgerufen wurde
        mock_file_dialog.assert_called_once()

        # Überprüfen, ob DataController.get_csv_data aufgerufen wurde
        self.main_window.data_controller.get_csv_data.assert_called_once()

        # Temporäre Datei löschen
        os.unlink(temp_path)

    def test_reset_data(self):
        """Testet die Rücksetzen-Funktion."""
        # Funktion aufrufen
        self.main_window.reset_data()

        # Überprüfen, ob DataController.reset aufgerufen wurde
        self.main_window.data_controller.reset.assert_called_once()

    @patch("src.main_window.QMessageBox")
    def test_show_error(self, mock_message_box):
        """Testet die Fehleranzeige."""
        # Mock für QMessageBox.critical einrichten
        mock_critical = MagicMock()
        mock_message_box.critical = mock_critical

        # Funktion aufrufen
        self.main_window.show_error("Testtitel", "Testmeldung")

        # Überprüfen, ob QMessageBox.critical aufgerufen wurde
        mock_critical.assert_called_once()
        args = mock_critical.call_args[0]
        self.assertEqual(args[0], self.main_window)  # parent
        self.assertEqual(args[1], "Testtitel")  # title
        self.assertEqual(args[2], "Testmeldung")  # message

    @patch("src.main_window.QMessageBox")
    def test_show_info(self, mock_message_box):
        """Testet die Infoanzeige."""
        # Mock für QMessageBox.information einrichten
        mock_info = MagicMock()
        mock_message_box.information = mock_info

        # Funktion aufrufen
        self.main_window.show_info("Testtitel", "Testmeldung")

        # Überprüfen, ob QMessageBox.information aufgerufen wurde
        mock_info.assert_called_once()
        args = mock_info.call_args[0]
        self.assertEqual(args[0], self.main_window)  # parent
        self.assertEqual(args[1], "Testtitel")  # title
        self.assertEqual(args[2], "Testmeldung")  # message


if __name__ == "__main__":
    unittest.main()
