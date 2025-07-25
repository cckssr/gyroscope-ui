#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Data controller for managing measurements and plot updates."""

from typing import Optional, List, Tuple, Dict, Union
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
            max_history: Maximum number of stored data points.
        """
        self.plot = plot_widget
        self.display = display_widget
        self.history = history_widget
        self.table = table_widget
        self.table_model: Optional[QStandardItemModel] = None
        self.data_points: List[Tuple[int, float, str]] = []
        self.max_history = max_history

        if self.table is not None:
            self.table_model = QStandardItemModel(0, 3, self.table)
            self.table_model.setHorizontalHeaderLabels(["Index", "Value (µs)", "Time"])
            self.table.setModel(self.table_model)

    def add_data_point(self, index: Union[int, str], value: Union[float, str]) -> None:
        """Add a new point and update the optional UI widgets.

        Args:
            index (Union[int, str]): Index of the data point.
            value (Union[float, str]): Value of the data point.
        """

        # Ensure numeric values
        try:
            # Check incoming data types
            index_num = int(index)
            value_num = float(value)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Add data and drop oldest when maximum size is reached
            self.data_points.append((index_num, value_num, timestamp))
            if len(self.data_points) > self.max_history:
                self.data_points.pop(0)

            # Update plot widget with all data points
            if self.plot:
                self.plot.update_plot(self.data_points)

            # Update current value display
            if self.display:
                self.display.display(value_num)

            # Update history list widget
            if self.history:
                # Insert new item at the top
                self.history.insertItem(0, f"{value_num} µs : {index_num}")
                self.history.item(0).setTextAlignment(Qt.AlignmentFlag.AlignRight)

                while self.history.count() > self.max_history:
                    self.history.takeItem(self.history.count() - 1)

            if self.table_model is not None:
                row = [
                    QStandardItem(str(index_num)),
                    QStandardItem(str(value_num)),
                    QStandardItem(timestamp),
                ]
                self.table_model.appendRow(row)
                while self.table_model.rowCount() > self.max_history:
                    self.table_model.removeRow(0)

        except (ValueError, TypeError) as e:
            Debug.error(f"Failed to convert values: {e}", exc_info=True)
        except (AttributeError, RuntimeError) as e:
            Debug.error(f"Failed to update UI elements: {e}", exc_info=True)

    def clear_data(self) -> None:
        """Clear all data points and reset optional widgets."""
        try:
            # Remove stored points
            self.data_points = []

            # Clear the plot
            if self.plot:
                self.plot.clear()

            # Reset displayed value
            if self.display:
                self.display.display(0)

            # Clear the history list
            if self.history:
                self.history.clear()

            if self.table_model is not None:
                while self.table_model.rowCount() > 0:
                    self.table_model.removeRow(0)

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
