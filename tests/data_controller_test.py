#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unit-Tests für die DataController-Klasse.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from PySide6.QtWidgets import QLCDNumber, QListWidget
from PySide6.QtCore import Qt

from src.data_controller import DataController, DataError


class TestDataController(unittest.TestCase):
    """Testfälle für die DataController-Klasse."""

    def setUp(self):
        """Testumgebung einrichten."""
        self.mock_lcd = Mock(spec=QLCDNumber)
        self.mock_history = Mock(spec=QListWidget)
        self.mock_plot = MagicMock()

        # DataController-Instanz erstellen
        self.data_controller = DataController(
            total_lcd=self.mock_lcd,
            history_widget=self.mock_history,
            plot_widget=self.mock_plot,
            max_history=100,
        )

    def test_init(self):
        """Testet die korrekte Initialisierung des DataController."""
        self.assertEqual(self.data_controller.count, 0)
        self.assertEqual(self.data_controller.history, [])
        self.assertEqual(self.data_controller.max_history, 100)
        self.assertIsNotNone(self.data_controller.total_lcd)
        self.assertIsNotNone(self.data_controller.history_widget)
        self.assertIsNotNone(self.data_controller.plot_widget)

    def test_add_value(self):
        """Testet das Hinzufügen von Werten."""
        # Wert hinzufügen und überprüfen
        self.data_controller.add_value(123, "Test Messung")

        # Überprüfen, ob die Anzahl aktualisiert wurde
        self.assertEqual(self.data_controller.count, 123)

        # Überprüfen, ob die History aktualisiert wurde
        self.assertEqual(len(self.data_controller.history), 1)

        # Überprüfen, ob das LCD aktualisiert wurde
        self.mock_lcd.display.assert_called_with(123)

        # Überprüfen, ob das History-Widget aktualisiert wurde
        self.mock_history.addItem.assert_called_once()

    def test_add_value_with_invalid_count(self):
        """Testet das Hinzufügen von ungültigen Werten."""
        with self.assertRaises(DataError):
            self.data_controller.add_value("invalid", "Test Messung")

    def test_reset(self):
        """Testet das Zurücksetzen des DataController."""
        # Erst ein paar Werte hinzufügen
        self.data_controller.add_value(123, "Test Messung 1")
        self.data_controller.add_value(456, "Test Messung 2")

        # Dann zurücksetzen
        self.data_controller.reset()

        # Überprüfen, ob alles zurückgesetzt wurde
        self.assertEqual(self.data_controller.count, 0)
        self.assertEqual(self.data_controller.history, [])

        # Überprüfen, ob die UI-Elemente aktualisiert wurden
        self.mock_lcd.display.assert_called_with(0)
        self.mock_history.clear.assert_called_once()
        self.mock_plot.clear.assert_called_once()

    def test_get_data_as_list(self):
        """Testet die Methode get_data_as_list."""
        # Werte hinzufügen
        self.data_controller.add_value(100, "Messung 1")
        self.data_controller.add_value(200, "Messung 2")

        # Daten abrufen
        data_list = self.data_controller.get_data_as_list()

        # Überprüfen, ob die Liste korrekt ist
        self.assertEqual(len(data_list), 2)
        self.assertEqual(data_list[0][0], "Messung 1")
        self.assertEqual(data_list[0][1], 100)
        self.assertEqual(data_list[1][0], "Messung 2")
        self.assertEqual(data_list[1][1], 200)

    def test_get_csv_data(self):
        """Testet die Methode get_csv_data."""
        # Werte hinzufügen
        self.data_controller.add_value(100, "Messung 1")
        self.data_controller.add_value(200, "Messung 2")

        # CSV-Daten abrufen
        csv_data = self.data_controller.get_csv_data()

        # Überprüfen, ob die CSV-Daten korrekt sind
        expected_header = ["Messung", "Anzahl"]
        expected_rows = [["Messung 1", "100"], ["Messung 2", "200"]]

        self.assertEqual(csv_data[0], expected_header)
        self.assertEqual(csv_data[1:], expected_rows)

    def test_history_limit(self):
        """Testet, ob die Begrenzung der Verlaufseinträge funktioniert."""
        # DataController mit maximal 2 Einträgen erstellen
        small_dc = DataController(
            total_lcd=self.mock_lcd,
            history_widget=self.mock_history,
            plot_widget=self.mock_plot,
            max_history=2,
        )

        # 3 Werte hinzufügen
        small_dc.add_value(100, "Messung 1")
        small_dc.add_value(200, "Messung 2")
        small_dc.add_value(300, "Messung 3")

        # Überprüfen, ob nur die neuesten 2 Einträge vorhanden sind
        self.assertEqual(len(small_dc.history), 2)
        self.assertEqual(small_dc.history[0][0], "Messung 2")
        self.assertEqual(small_dc.history[1][0], "Messung 3")


if __name__ == "__main__":
    unittest.main()
