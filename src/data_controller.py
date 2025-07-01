#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Data controller for managing measurements and plot updates."""

from typing import Optional, List, Tuple, Dict, Union
import queue
import threading
from time import time

try:  # pragma: no cover - optional dependency for headless testing
    from PySide6.QtWidgets import QLCDNumber, QListWidget  # type: ignore
    from PySide6.QtCore import Qt, QTimer  # type: ignore
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
        max_history: int = MAX_HISTORY_SIZE,
        gui_update_interval: int = 200,  # ms (optimiert für Performance)
    ):
        """Initialise the data controller.

        Args:
            plot_widget: Plotting widget used for visualisation.
            display_widget: Optional LCD display for the current value.
            history_widget: Optional list widget for history display.
            max_history: Maximum number of data points for GUI display (not file storage).
            gui_update_interval: GUI update interval in milliseconds.
        """
        self.plot = plot_widget
        self.display = display_widget
        self.history = history_widget

        # Vollständige Datenspeicherung (für CSV-Export, etc.)
        self.data_points: List[Tuple[int, float]] = []

        # GUI-limitierte Daten (für Plot und History Widget)
        self.gui_data_points: List[Tuple[int, float]] = []
        self.max_history = max_history

        # Queue für hochfrequente Datenerfassung
        self.data_queue: queue.Queue = queue.Queue()
        self._queue_lock = threading.Lock()
        self._last_update_time = time()

        # Timer für GUI-Updates alle 100ms
        try:
            self.gui_update_timer = QTimer()
            if hasattr(self.gui_update_timer.timeout, "connect"):
                self.gui_update_timer.timeout.connect(self._process_queued_data)
                self.gui_update_timer.start(gui_update_interval)
            else:
                self.gui_update_timer = None
        except Exception:
            # Fallback für headless testing
            self.gui_update_timer = None
            Debug.info("GUI update timer not available (headless mode)")

        # Performance-Zähler
        self._total_points_received = 0
        self._points_processed_in_last_update = 0

    def add_data_point_fast(
        self, index: Union[int, str], value: Union[float, str]
    ) -> None:
        """Schnelles Hinzufügen von Datenpunkten in die Queue ohne GUI-Update.

        Diese Methode ist für hochfrequente Datenerfassung optimiert und aktualisiert
        die GUI nicht sofort. Stattdessen werden die Daten in eine Queue eingereiht
        und alle 100ms verarbeitet.

        Args:
            index: Der Datenpunktindex
            value: Der gemessene Wert
        """
        try:
            # Schnelle Validierung und Konvertierung
            index_num = int(index)
            value_num = float(value)

            # Thread-sicher in Queue einreihen
            with self._queue_lock:
                self.data_queue.put((index_num, value_num, time()))
                self._total_points_received += 1

        except (ValueError, TypeError) as e:
            Debug.error(f"Failed to convert values for fast queue: {e}")

    def _process_queued_data(self) -> None:
        """Verarbeitet alle Daten aus der Queue und aktualisiert die GUI."""
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
                        new_points.append((index_num, value_num))
                    except queue.Empty:
                        break

            if not new_points:
                return

            self._points_processed_in_last_update = len(new_points)

            # Alle neuen Punkte zu den vollständigen Daten hinzufügen (für CSV-Export)
            for index_num, value_num in new_points:
                self.data_points.append((index_num, value_num))

            # Alle neuen Punkte auch zu GUI-Daten hinzufügen (mit Limit)
            for index_num, value_num in new_points:
                self.gui_data_points.append((index_num, value_num))

            # Nur GUI-Daten begrenzen, vollständige Daten bleiben unbegrenzt
            while len(self.gui_data_points) > self.max_history:
                self.gui_data_points.pop(0)

            # GUI nur einmal mit dem letzten Wert aktualisieren
            if new_points:
                last_index, last_value = new_points[-1]
                self._update_gui_widgets(last_index, last_value)

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

    def _update_gui_widgets(self, index: int, value: float) -> None:
        """Aktualisiert die GUI-Widgets mit einem einzelnen Datenpunkt."""
        try:
            # Update plot widget - alle neuen Punkte in einem Batch hinzufügen
            if self.plot and self._points_processed_in_last_update > 0:
                # Hole alle neuen Punkte für den Plot-Update (aus GUI-limitierten Daten)
                new_plot_points = self.gui_data_points[
                    -self._points_processed_in_last_update :
                ]

                # Verwende die effiziente Batch-Update-Methode wenn verfügbar
                if hasattr(self.plot, "update_plot_batch"):
                    self.plot.update_plot_batch(new_plot_points)
                else:
                    # Fallback für alte PlotWidget-Versionen
                    for point in new_plot_points:
                        self.plot.update_plot(point)

            # Update current value display mit dem letzten Wert
            if self.display:
                self.display.display(value)

            # Update history list widget mit dem letzten Wert
            if self.history:
                # Insert new item at the top
                self.history.insertItem(0, f"{value} µs : {index}")
                # Right align text for readability
                self.history.item(0).setTextAlignment(Qt.AlignmentFlag.AlignRight)

                # Keep list size within limit
                while self.history.count() > self.max_history:
                    self.history.takeItem(self.history.count() - 1)

        except (AttributeError, RuntimeError) as e:
            Debug.error(f"Failed to update GUI widgets: {e}", exc_info=True)

    def add_data_point(self, index: Union[int, str], value: Union[float, str]) -> None:
        """Add a new point and update the optional UI widgets.

        Hinweis: Diese Methode ist für Kompatibilität beibehalten. Für hochfrequente
        Datenerfassung sollte add_data_point_fast() verwendet werden.
        """

        # Ensure numeric values
        try:
            # Sicherstellen, dass die Werte numerisch sind
            index_num = int(index)
            value_num = float(value)

            # Add data to full storage (unbounded for file saving)
            self.data_points.append((index_num, value_num))

            # Add data to GUI storage (bounded for display)
            self.gui_data_points.append((index_num, value_num))
            if len(self.gui_data_points) > self.max_history:
                self.gui_data_points.pop(0)

            # Update GUI widgets
            self._update_gui_widgets(index_num, value_num)

        except (ValueError, TypeError) as e:
            Debug.error(f"Failed to convert values: {e}", exc_info=True)
        except (AttributeError, RuntimeError) as e:
            Debug.error(f"Failed to update UI elements: {e}", exc_info=True)

    def stop_gui_updates(self) -> None:
        """Stoppt den GUI-Update-Timer."""
        if hasattr(self, "gui_update_timer") and self.gui_update_timer is not None:
            try:
                self.gui_update_timer.stop()
                Debug.debug("GUI update timer stopped")
            except Exception as e:
                Debug.debug(f"Error stopping GUI timer: {e}")

    def start_gui_updates(self, interval: int = 100) -> None:
        """Startet den GUI-Update-Timer."""
        if hasattr(self, "gui_update_timer") and self.gui_update_timer is not None:
            try:
                self.gui_update_timer.start(interval)
                Debug.debug(f"GUI update timer started with {interval}ms interval")
            except Exception as e:
                Debug.debug(f"Error starting GUI timer: {e}")

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

    def get_data_as_list(self) -> List[Tuple[int, float]]:
        """Return all stored data points as a list."""
        return self.data_points.copy()

    def get_csv_data(self) -> List[List[str]]:
        """Prepare the stored data for CSV export."""
        result: List[List[str]] = [["Index", "Value (µs)"]]
        for idx, value in self.data_points:
            result.append([str(idx), str(value)])
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

    def get_all_data_for_export(self) -> List[Tuple[int, float]]:
        """
        Gibt alle Datenpunkte für den Export zurück (unbegrenzt).

        Returns:
            List[Tuple[int, float]]: Alle Datenpunkte von Start bis Stop
        """
        return self.data_points.copy()
