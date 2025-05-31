#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DataController-Modul zum Verwalten von Messdaten und Plotaktualisierungen.
"""

from typing import Optional, List, Tuple, Dict, Union

from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QLCDNumber,
    QListWidget,
)
from PySide6.QtCore import Qt  # pylint: disable=no-name-in-module

from src.plot import PlotWidget
from src.debug_utils import Debug

# Konfigurationswerte direkt definieren, um Import-Probleme zu umgehen
MAX_HISTORY_SIZE = 100


class DataController:
    """
    Verwaltet Messdaten und Plotaktualisierungen.

    Diese Klasse ist verantwortlich für:
    1. Speicherung und Verwaltung von Datenpunkten
    2. Aktualisierung der UI-Elemente (Plot, Anzeige, Historie)
    3. Berechnung statistischer Werte
    """

    def __init__(
        self,
        plot_widget: PlotWidget,
        display_widget: Optional[QLCDNumber] = None,
        history_widget: Optional[QListWidget] = None,
        max_history: int = MAX_HISTORY_SIZE,
    ):
        """
        Initialisiert den DataController.

        Args:
            plot_widget (PlotWidget): Das Widget zur Darstellung von Daten
            display_widget (QLCDNumber, optional): Widget für die aktuelle Wertanzeige
            history_widget (QListWidget, optional): Widget für die Anzeige der Datenhistorie
            max_history (int, optional): Maximale Anzahl gespeicherter Datenpunkte
        """
        self.plot = plot_widget
        self.display = display_widget
        self.history = history_widget
        self.data_points: List[Tuple[int, float]] = []
        self.max_history = max_history

    def add_data_point(self, index: Union[int, str], value: Union[float, str]) -> None:
        """
        Fügt einen neuen Datenpunkt hinzu und aktualisiert UI-Elemente.

        Args:
            index (int oder str): Der x-Wert (üblicherweise ein Zähler)
            value (float oder str): Der gemessene Wert
        """
        try:
            # Sicherstellen, dass die Werte numerisch sind
            index_num = int(index)
            value_num = float(value)

            # Datenpunkt hinzufügen und älteste entfernen, wenn Maximum erreicht
            self.data_points.append((index_num, value_num))
            if len(self.data_points) > self.max_history:
                self.data_points.pop(0)

            # Plot aktualisieren
            if self.plot:
                self.plot.update_plot((index_num, value_num))

            # Anzeige des aktuellen Wertes aktualisieren
            if self.display:
                self.display.display(value_num)

            # Historieliste mit korrektem Format aktualisieren
            if self.history:
                # Neues Element am Anfang einfügen
                self.history.insertItem(0, f"{value_num} µs : {index_num}")
                # Rechtsbündige Textausrichtung für bessere Lesbarkeit
                self.history.item(0).setTextAlignment(Qt.AlignmentFlag.AlignRight)

                # Listengröße begrenzen
                while self.history.count() > self.max_history:
                    self.history.takeItem(self.history.count() - 1)

        except (ValueError, TypeError) as e:
            Debug.error(
                f"Fehler bei der Konvertierung der Datenpunktwerte: {e}", exc_info=True
            )
        except (AttributeError, RuntimeError) as e:
            Debug.error(
                f"Fehler beim Aktualisieren der UI-Elemente: {e}", exc_info=True
            )

    def clear_data(self) -> None:
        """
        Löscht alle Datenpunkte und setzt UI-Elemente zurück.
        """
        try:
            # Datenpunkte löschen
            self.data_points = []

            # Plot zurücksetzen
            if self.plot:
                self.plot.clear()

            # Displaywert zurücksetzen
            if self.display:
                self.display.display(0)

            # Historieliste löschen
            if self.history:
                self.history.clear()

        except (AttributeError, RuntimeError) as e:
            Debug.error(f"Fehler beim Zurücksetzen der UI-Elemente: {e}", exc_info=True)

    def get_statistics(self) -> Dict[str, float]:
        """
        Berechnet statistische Kennzahlen aus den vorhandenen Datenpunkten.

        Returns:
            dict: Ein Dictionary mit statistischen Werten (count, min, max, avg, stdev)
        """
        # Initialisieren mit Standardwerten als Gleitkommazahlen
        stats: Dict[str, float] = {
            "count": float(len(self.data_points)),
            "min": 0.0,
            "max": 0.0,
            "avg": 0.0,
            "stdev": 0.0,
        }

        if self.data_points:
            try:
                # Werte extrahieren (zweites Element jedes Tupels)
                values = [float(point[1]) for point in self.data_points]

                # Grundlegende Statistiken berechnen
                stats["min"] = min(values)
                stats["max"] = max(values)
                stats["avg"] = sum(values) / len(values)

                # Standardabweichung berechnen (wenn mehr als ein Wert verfügbar)
                if len(values) > 1:
                    mean = stats["avg"]
                    variance = sum((x - mean) ** 2 for x in values) / len(values)
                    stats["stdev"] = variance**0.5
            except (ValueError, TypeError) as e:
                Debug.error(
                    f"Fehler bei der Konvertierung von Werten: {e}", exc_info=True
                )
            except (ZeroDivisionError, OverflowError) as e:
                Debug.error(
                    f"Mathematischer Fehler bei der Statistikberechnung: {e}",
                    exc_info=True,
                )

        return stats

    def get_data_as_list(self) -> List[Tuple[int, float]]:
        """
        Gibt alle gespeicherten Datenpunkte als Liste zurück.

        Returns:
            list: Liste aller Datenpunkte als (Index, Wert)-Tupel
        """
        return self.data_points.copy()

    def get_csv_data(self) -> List[List[str]]:
        """
        Bereitet die Daten für den Export als CSV vor.

        Returns:
            list: Liste von Zeilen, wobei die erste Zeile Header-Informationen enthält
        """
        # Header-Zeile
        result: List[List[str]] = [["Index", "Wert (µs)"]]

        # Datenpunkte hinzufügen
        for idx, value in self.data_points:
            result.append([str(idx), str(value)])

        return result
