#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Data controller for managing measurements and plot updates."""

from typing import Optional, List, Tuple, Dict, Union
import queue
import threading
from time import time
from datetime import datetime

try:  # pragma: no cover - optional dependency for headless testing
    from PySide6.QtWidgets import (
        QLCDNumber,
        QListWidget,
        QTableView,
    )  # type: ignore
    from PySide6.QtGui import QStandardItemModel, QStandardItem  # type: ignore
    from PySide6.QtCore import Qt  # type: ignore


except Exception:  # ImportError or missing Qt libraries

    class QLCDNumber:  # pragma: no cover - fallback stub
        def display(self, *args, **kwargs):
            pass

    class QListWidget:  # pragma: no cover - fallback stub
        def insertItem(self, *args, **kwargs):
            pass

        def item(self, *args, **kwargs):
            class _Item:
                def setTextAlignment(self, *a, **k):
                    pass

            return _Item()

        def count(self) -> int:
            return 0

        def takeItem(self, *args, **kwargs):
            pass

        def clear(self):
            pass

    class QTableView:  # pragma: no cover - fallback stub
        def setModel(self, *args, **kwargs):
            pass

    class QStandardItemModel:  # pragma: no cover - fallback stub
        def __init__(self, *args, **kwargs):
            pass

        def setHorizontalHeaderLabels(self, *args, **kwargs):
            pass

        def appendRow(self, *args, **kwargs):
            pass

        def rowCount(self):
            return 0

        def removeRow(self, *args, **kwargs):
            pass

    class _Alignment:
        AlignRight = 0

    class _Qt:
        AlignmentFlag = _Alignment

    class QTimer:  # pragma: no cover - fallback stub
        def __init__(self):
            self.timeout = self._MockSignal()

        def start(self, interval):
            pass

        def stop(self):
            pass

        class _MockSignal:
            def connect(self, callback):
                pass

    Qt = _Qt()

from src.plot import PlotWidget
from src.debug_utils import Debug

# Konfigurationswerte direkt definieren, um Import-Probleme zu umgehen
MAX_HISTORY_SIZE = 100


class DataController:
    """Store measurement data and provide statistics for the UI."""

    def __init__(
        self,
        plot_widget: PlotWidget,
        display_widget: Optional[QLCDNumber] = None,
        history_widget: Optional[QListWidget] = None,
        table_widget: Optional[QTableView] = None,
        max_history: int = MAX_HISTORY_SIZE,
    ):
        """Initialise the data controller.

        Args:
            plot_widget: Plotting widget used for visualisation.
            display_widget: Optional LCD display for the current value.
            history_widget: Optional list widget for history display.
            max_history: Maximum number of data points for GUI display (not file storage).
        """
        self.plot = plot_widget
        self.display = display_widget
        self.history = history_widget
        self.table = table_widget
        self.table_model: Optional[QStandardItemModel] = None
        self.max_history = max_history

        # Vollständige Datenspeicherung (für CSV-Export, unbegrenzt)
        self.data_points: List[Tuple[int, float, str]] = []

        # GUI-limitierte Daten (für Plot und History Widget, begrenzt)
        self.gui_data_points: List[Tuple[int, float, str]] = []

        # Queue für hochfrequente Datenerfassung
        self.data_queue: queue.Queue = queue.Queue()
        self._queue_lock = threading.Lock()
        self._last_update_time = time()

        # Performance-Zähler
        self._total_points_received = 0
        self._points_processed_in_last_update = 0

        if self.table is not None:
            self.table_model = QStandardItemModel(0, 3, self.table)
            self.table_model.setHorizontalHeaderLabels(["Index", "Value (µs)", "Time"])
            self.table.setModel(self.table_model)

    def add_data_point_fast(
        self, index: Union[int, str], value: Union[float, str]
    ) -> None:
        """Schnelles Hinzufügen von Datenpunkten in die Queue ohne GUI-Update.

        Diese Methode ist für hochfrequente Datenerfassung optimiert und fügt
        die Daten sofort zur vollständigen Speicherung hinzu und in eine Queue
        für die GUI-Updates.

        Args:
            index: Der Datenpunktindex
            value: Der gemessene Wert
        """
        try:
            # Schnelle Validierung und Konvertierung
            index_num = int(index)
            value_num = float(value)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Vollständige Daten sofort hinzufügen (für CSV-Export, unbegrenzt)
            self.data_points.append((index_num, value_num, timestamp))

            # Thread-sicher in Queue einreihen für GUI-Updates
            with self._queue_lock:
                self.data_queue.put((index_num, value_num, timestamp))
                self._total_points_received += 1

        except (ValueError, TypeError) as e:
            Debug.error(f"Failed to convert values for fast queue: {e}")

    def process_queued_data(self) -> None:
        """Verarbeitet alle Daten aus der Queue und aktualisiert die GUI.

        Diese Methode sollte regelmäßig von der aufrufenden Anwendung aufgerufen werden,
        um die GUI mit den neuesten Daten zu aktualisieren.
        """
        if self.data_queue.empty():
            return

        new_points = []
        current_time = time()

        try:
            # Alle verfügbaren Datenpunkte aus der Queue holen
            with self._queue_lock:
                while not self.data_queue.empty():
                    try:
                        index_num, value_num, timestamp = self.data_queue.get_nowait()
                        new_points.append((index_num, value_num, timestamp))
                    except queue.Empty:
                        break

            if not new_points:
                return

            self._points_processed_in_last_update = len(new_points)

            # Alle neuen Punkte zu GUI-Daten hinzufügen (mit Limit)
            for index_num, value_num, timestamp in new_points:
                self.gui_data_points.append((index_num, value_num, timestamp))

            # Nur GUI-Daten begrenzen, vollständige Daten bleiben unbegrenzt
            while len(self.gui_data_points) > self.max_history:
                self.gui_data_points.pop(0)

            # GUI nur einmal mit dem letzten Wert aktualisieren
            if new_points:
                last_index, last_value, last_timestamp = new_points[-1]
                self._update_gui_widgets(last_index, last_value, last_timestamp)

            # Performance-Logging
            time_since_last = current_time - self._last_update_time
            if time_since_last > 0:
                rate = len(new_points) / time_since_last
                Debug.debug(
                    f"Processed {len(new_points)} points in {time_since_last:.3f}s "
                    f"(rate: {rate:.1f} Hz, total: {self._total_points_received})"
                )

            self._last_update_time = current_time

        except Exception as e:
            Debug.error(f"Error processing queued data: {e}", exc_info=True)

    def has_queued_data(self) -> bool:
        """
        Überprüft, ob Daten in der Queue vorhanden sind.

        Returns:
            bool: True wenn Daten in der Queue sind, False sonst
        """
        return not self.data_queue.empty()

    def get_queue_size(self) -> int:
        """
        Gibt die aktuelle Größe der Queue zurück.

        Returns:
            int: Anzahl der Elemente in der Queue
        """
        with self._queue_lock:
            return self.data_queue.qsize()

    def _update_gui_widgets(self, index: int, value: float, timestamp: str) -> None:
        """Aktualisiert die GUI-Widgets mit einem einzelnen Datenpunkt."""
        try:
            # Update plot widget - alle GUI-Daten für komplette Aktualisierung verwenden
            if self.plot and len(self.gui_data_points) > 0:
                # Verwende die effiziente Batch-Update-Methode wenn verfügbar
                if hasattr(self.plot, "update_plot_batch"):
                    self.plot.update_plot_batch(self.gui_data_points)
                else:
                    # Fallback: Plot mit allen GUI-Daten aktualisieren
                    self.plot.update_plot(self.gui_data_points)

            # Update current value display mit dem letzten Wert
            if self.display:
                self.display.display(value)

            # Update history list widget mit dem letzten Wert
            if self.history:
                # Insert new item at the top
                self.history.insertItem(0, f"{value} µs : {index}")
                # Right align text for readability
                self.history.item(0).setTextAlignment(Qt.AlignmentFlag.AlignRight)

                while self.history.count() > self.max_history:
                    self.history.takeItem(self.history.count() - 1)

            # Update table model with new data
            if self.table_model is not None:
                try:
                    row = [
                        QStandardItem(str(index)),
                        QStandardItem(str(value)),
                        QStandardItem(timestamp),
                    ]
                    self.table_model.appendRow(row)
                    while self.table_model.rowCount() > self.max_history:
                        self.table_model.removeRow(0)
                except Exception as table_error:
                    Debug.error(
                        f"Failed to update table model: {table_error}", exc_info=True
                    )

        except (AttributeError, RuntimeError) as e:
            Debug.error(f"Failed to update GUI widgets: {e}", exc_info=True)

    def add_data_point(self, index: Union[int, str], value: Union[float, str]) -> None:
        """Add a new point and update the optional UI widgets.

        Hinweis: Diese Methode ist für direkte GUI-Updates gedacht. Für hochfrequente
        Datenerfassung sollte add_data_point_fast() verwendet werden.
        """

        # Ensure numeric values
        try:
            # Sicherstellen, dass die Werte numerisch sind
            index_num = int(index)
            value_num = float(value)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Add data to full storage (unbounded for file saving)
            self.data_points.append((index_num, value_num, timestamp))

            # Add data to GUI storage (bounded for display)
            self.gui_data_points.append((index_num, value_num, timestamp))
            if len(self.gui_data_points) > self.max_history:
                self.gui_data_points.pop(0)

            # Update GUI widgets directly
            self._update_gui_widgets(index_num, value_num, timestamp)

        except (ValueError, TypeError) as e:
            Debug.error(f"Failed to convert values: {e}", exc_info=True)
        except (AttributeError, RuntimeError) as e:
            Debug.error(f"Failed to update UI elements: {e}", exc_info=True)

    def clear_data(self) -> None:
        """Clear all data points and reset optional widgets."""
        try:
            # Remove stored points (both full and GUI data)
            self.data_points = []
            self.gui_data_points = []

            # Clear the queue
            with self._queue_lock:
                while not self.data_queue.empty():
                    try:
                        self.data_queue.get_nowait()
                    except queue.Empty:
                        break

            # Reset counters
            self._total_points_received = 0
            self._points_processed_in_last_update = 0
            self._last_update_time = time()

            # Clear the plot
            if self.plot:
                self.plot.clear()

            # Reset displayed value
            if self.display:
                self.display.display(0)

            # Clear the history list
            if self.history:
                self.history.clear()

            # Clear the table model
            if self.table_model is not None:
                try:
                    while self.table_model.rowCount() > 0:
                        self.table_model.removeRow(0)
                except Exception as table_error:
                    Debug.error(
                        f"Failed to clear table model: {table_error}", exc_info=True
                    )

        except (AttributeError, RuntimeError) as e:
            Debug.error(f"Failed to reset UI elements: {e}", exc_info=True)

    def get_statistics(self) -> Dict[str, float]:
        """Return basic statistics for the stored data."""
        # Initialise statistics with defaults
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
                Debug.error(f"Value conversion error: {e}", exc_info=True)
            except (ZeroDivisionError, OverflowError) as e:
                Debug.error(
                    f"Statistical calculation error: {e}",
                    exc_info=True,
                )

        return stats

    def get_data_as_list(self) -> List[Tuple[int, float, str]]:
        """Return all stored data points as a list."""
        return self.data_points.copy()

    def get_csv_data(self) -> List[List[str]]:
        """Prepare the stored data for CSV export."""
        result: List[List[str]] = [["Index", "Value (µs)", "Time"]]
        for idx, value, timestamp in self.data_points:
            result.append([str(idx), str(value), timestamp])
        return result

    def get_performance_stats(self) -> Dict[str, Union[int, float]]:
        """Gibt Performance-Statistiken für die Datenerfassung zurück."""
        queue_size = 0
        with self._queue_lock:
            queue_size = self.data_queue.qsize()

        return {
            "total_points_received": self._total_points_received,
            "points_in_last_update": self._points_processed_in_last_update,
            "queue_size": queue_size,
            "stored_points": len(self.data_points),
            "last_update_time": self._last_update_time,
        }

    def get_data_info(self) -> dict:
        """
        Gibt Informationen über die gespeicherten Daten zurück.

        Returns:
            dict: Informationen über vollständige und GUI-Daten
        """
        return {
            "total_data_points": len(self.data_points),
            "gui_data_points": len(self.gui_data_points),
            "max_history_limit": self.max_history,
            "data_points_for_export": self.data_points,  # Vollständige Daten für CSV-Export
            "gui_points_for_display": self.gui_data_points,  # Begrenzte Daten für GUI
        }

    def get_all_data_for_export(self) -> List[Tuple[int, float, str]]:
        """
        Gibt alle Datenpunkte für den Export zurück (unbegrenzt).

        Returns:
            List[Tuple[int, float, str]]: Alle Datenpunkte von Start bis Stop mit Zeitstempel
        """
        return self.data_points.copy()
