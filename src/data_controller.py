#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Data controller for managing measurements and plot updates."""

from typing import Optional, List, Tuple, Dict, Union
import math
import queue
import threading
from time import time
from datetime import datetime

from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QLCDNumber,
    QTableView,
)  # type: ignore
from PySide6.QtGui import (  # pylint: disable=no-name-in-module
    QStandardItemModel,
    QStandardItem,
)
from PySide6.QtCore import QTimer  # pylint: disable=no-name-in-module

from .plot import PlotWidget
from .debug_utils import Debug
from .helper_classes import (
    SaveManager,
    import_config,
    create_dropbox_foldername,
    MessageHelper,
)

# Konfigurationswerte direkt definieren, um Import-Probleme zu umgehen
MAX_HISTORY_SIZE = 100
CONFIG = import_config()


class DataController:
    """Store measurement data and provide statistics for the UI.

    Now includes integrated SaveManager functionality for better cohesion.
    """

    def __init__(
        self,
        frequency_plot: Optional[PlotWidget],
        gyroscope_plot: Optional[PlotWidget],
        display_widget: Optional[QLCDNumber] = None,
        table_widget: Optional[QTableView] = None,
        max_history: int = MAX_HISTORY_SIZE,
        gui_update_interval: int = 200,  # ms (optimised for performance)
    ):
        """Initialise the data controller.

        Args:
            plot_widget: Plotting widget used for visualisation.
            display_widget: Optional LCD display for the current value.
            history_widget: Optional list widget for history display.
            max_history: Maximum number of data points for GUI display (not file storage).
        """
        # Core widgets
        self.f_plot = frequency_plot
        self.g_plot = gyroscope_plot
        self.display = display_widget
        self.table = table_widget
        self.table_model: Optional[QStandardItemModel] = None
        self.max_history = max_history

        # ---------------- Internal Storage ----------------
        # Export buffer (only when recording True)
        self.data_points: List[Tuple[float, float, float]] = []
        # Live plot series (rolling window, always filled)
        self.freq_series: List[Tuple[float, float, str]] = []
        self.gyro_series: List[Tuple[float, float, str]] = []

        # Recording flag
        self.recording: bool = False

        # Integrated SaveManager
        self.save_manager = SaveManager(
            base_dir=CONFIG["data_controller"]["default_save_dir"]
        )
        self.measurement_start: Optional[datetime] = None
        self.measurement_end: Optional[datetime] = None

        # Performance metrics placeholders
        self._total_points_received: int = 0
        self._points_processed_in_last_update: int = 0

        # Queue infra (minimal)
        self.data_queue: queue.Queue = queue.Queue()
        self._queue_lock = threading.Lock()
        self._last_update_time = time()

        # Removed history widget placeholder
        self.history = None

        # Optional timer (not currently used for batching)
        try:
            self.gui_update_timer = QTimer()
            if gui_update_interval > 0:
                self.gui_update_timer.setInterval(gui_update_interval)
        except Exception:  # pragma: no cover
            self.gui_update_timer = None

        if self.table is not None:
            self.table_model = QStandardItemModel(0, 3, self.table)
            self.table_model.setHorizontalHeaderLabels(["Time (s)", "Value", "Stamp"])
            self.table.setModel(self.table_model)

    # ------------------------------------------------------------------
    # New multi-signal callback (elapsed_time_s, frequency, accel_z, gyro_z)
    # ------------------------------------------------------------------
    def handle_multi_data_point(
        self, elapsed_s: float, frequency: float, accel_z: float, gyro_z: float
    ) -> None:
        """Handle a multi channel data update.

        Stores the full tuple and updates two plots:
        - frequency_plot: time vs frequency (Hz)
        - gyroscope_plot: time vs gyro Z (°/s)
        NaN values are skipped for their respective series.
        """
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        Debug.debug(
            f"multi_data_point recv t={elapsed_s:.3f} f={frequency:.3f} gyroZ={gyro_z:.3f} rec={'on' if self.recording else 'off'}"
        )
        if self.recording:
            self.data_points.append((elapsed_s, frequency, gyro_z))
            Debug.debug(
                f"Data point added to storage. Total points: {len(self.data_points)}"
            )

        # -------- Fallback Logik für leere Kanäle --------
        # Wenn frequency NaN ist, aber accel_z vorhanden, nutze accel_z ersatzweise im Frequenz-Plot,
        # damit der Nutzer überhaupt Aktivität sieht.
        freq_for_plot = frequency
        used_fallback = False
        if math.isnan(freq_for_plot) and not math.isnan(accel_z):
            freq_for_plot = accel_z
            used_fallback = True

        if not math.isnan(freq_for_plot):
            self.freq_series.append((elapsed_s, freq_for_plot, ts))
            if len(self.freq_series) > self.max_history:
                self.freq_series = self.freq_series[-self.max_history :]
            if used_fallback:
                Debug.debug("Frequency fallback -> accel_z für Plot verwendet")

        # Gyro Z series
        if not math.isnan(gyro_z):
            self.gyro_series.append((elapsed_s, gyro_z, ts))
            if len(self.gyro_series) > self.max_history:
                self.gyro_series = self.gyro_series[-self.max_history :]
        else:
            if math.isnan(freq_for_plot):
                Debug.debug("Alle Kanäle NaN – nichts zu plotten in diesem Schritt")

        # Update plots immediately (could be rate-limited if needed)
        try:
            if self.f_plot and self.freq_series:
                self.f_plot.update_plot(self.freq_series)
            if self.g_plot and self.gyro_series:
                self.g_plot.update_plot(self.gyro_series)
        except Exception as e:  # pragma: no cover
            Debug.error(f"Plot update failed: {e}")

    # Legacy single-value interfaces (no-op or thin wrappers) -----------------
    def add_data_point_fast(self, *_args, **_kwargs) -> None:  # pragma: no cover
        Debug.debug("add_data_point_fast legacy call ignored (multi-mode active)")

    def _process_queued_data(self) -> None:  # pragma: no cover
        pass

    def _update_gui_widgets(self, t_sec: float, value: float, timestamp: str) -> None:
        """Update value display and table (plots handled in multi callback)."""
        try:
            # Update current value display with the last value
            if self.display:
                self.display.display(value)

            # Update table model with new data
            if self.table_model is not None:
                try:
                    row = [
                        QStandardItem(f"{t_sec:.3f}"),
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

    def add_data_point(self, *_, **__):  # pragma: no cover
        Debug.debug("add_data_point legacy call ignored (multi-mode active)")

    def stop_gui_updates(self) -> None:
        """Stop the GUI update timer."""
        if hasattr(self, "gui_update_timer") and self.gui_update_timer is not None:
            try:
                self.gui_update_timer.stop()
                Debug.debug("GUI update timer stopped")
            except Exception as e:
                Debug.debug(f"Error stopping GUI timer: {e}")

    def start_gui_updates(self, interval: int = 100) -> None:
        """Start the GUI update timer."""
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
            self.freq_series = []
            self.gyro_series = []

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
            if self.f_plot:
                self.f_plot.clear()
            if self.g_plot:
                self.g_plot.clear()

            # Reset displayed value
            if self.display:
                self.display.display(0)

            # Clear the history list
            if getattr(self, "history", None):
                try:
                    self.history.clear()  # type: ignore[union-attr]
                except Exception:  # pragma: no cover
                    pass

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

    # (Recording control methods defined at class scope below)

    def stop_recording(self) -> None:
        """Stop recording (plots continue updating live)."""
        self.recording = False
        Debug.debug(
            f"Recording stopped. Stored points: {len(self.data_points)} (plots continue)"
        )

    # ---------------- Recording Control (exposed API) -----------------
    def clear_storage_only(self) -> None:
        """Clear only export buffer; keep live plot history intact."""
        self.data_points = []
        Debug.debug("Export-Puffer geleert (Live-Daten bleiben sichtbar)")

    def start_recording(self) -> None:
        """Start filling export buffer (live plotting always active)."""
        self.recording = True
        Debug.debug("Recording started (export buffer will fill)")

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

                # Calculate basic statistics
                stats["min"] = min(values)
                stats["max"] = max(values)
                stats["avg"] = sum(values) / len(values)

                # Calculate standard deviation (if more than one value available)
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

    def get_data_as_list(self) -> List[Tuple[float, float, float]]:
        """Return all stored multi-channel data points as a list."""
        return self.data_points.copy()

    def get_csv_data(self) -> List[List[str]]:
        """Prepare the stored data for CSV export."""
        result: List[List[str]] = [
            ["Time (s)", "Disk rotation frequency (Hz)", "Gyro Z rate (rad/s)"]
        ]
        for t_s, freq, gyro_z in self.data_points:
            result.append(
                [
                    f"{t_s:.6f}",
                    f"{freq:.6f}" if not math.isnan(freq) else "",
                    f"{gyro_z:.6f}" if not math.isnan(gyro_z) else "",
                ]
            )
        return result

    def get_performance_stats(self) -> Dict[str, Union[int, float]]:
        """Return performance statistics for data acquisition."""
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
        """Return information about the stored data."""
        return {
            "total_data_points": len(self.data_points),
            "frequency_points": len(self.freq_series),
            "gyro_points": len(self.gyro_series),
            "max_history_limit": self.max_history,
            "data_points_for_export": self.data_points,
        }

    def get_all_data_for_export(self) -> List[Tuple[float, float, float]]:
        """Return all collected multi-channel data points."""
        return self.data_points.copy()

    def get_current_values(self) -> Dict[str, Union[float, int]]:
        """Get current data point values for GUI display.

        Returns:
            Dictionary with current values:
            - data_points_count: Number of total data points (recorded)
            - current_frequency: Latest frequency value (Hz) from live data
            - current_gyro_z: Latest gyro Z value (°/s) from live data
        """
        Debug.debug(
            f"get_current_values called, data_points length: {len(self.data_points)}, freq_series: {len(self.freq_series)}, gyro_series: {len(self.gyro_series)}"
        )

        # Default values
        values = {
            "data_points_count": len(self.data_points),  # Only recorded data
            "current_frequency": 0.0,
            "current_gyro_z": 0.0,
        }

        # Get latest frequency from live plot data (always available)
        if self.freq_series:
            latest_freq = self.freq_series[-1]  # (elapsed_s, frequency, timestamp)
            values["current_frequency"] = latest_freq[1]
            Debug.debug(f"Using frequency from freq_series: {latest_freq[1]}")
        else:
            Debug.debug("No frequency data in freq_series")

        # Get latest gyro_z from live plot data (always available)
        if self.gyro_series:
            latest_gyro = self.gyro_series[-1]  # (elapsed_s, gyro_z, timestamp)
            values["current_gyro_z"] = latest_gyro[1]
            Debug.debug(f"Using gyro_z from gyro_series: {latest_gyro[1]}")
        else:
            Debug.debug("No gyro_z data in gyro_series")

        Debug.debug(f"Returning values: {values}")
        return values

    # ============= Integrated SaveManager Methods =============

    def save_measurement_auto(
        self, group_letter: str, subterm: str = "", suffix: str = ""
    ):
        """Auto-save measurement with current data.

        Args:
            group_letter: Group identifier
            subterm: Subgroup term
            suffix: Optional suffix for filename

        Returns:
            Path to saved file or None if failed
        """
        if not self.save_manager.auto_save or self.save_manager.last_saved:
            return None

        data = self.get_csv_data()
        measurement_name = "Messung"

        saved_path = self.save_manager.auto_save_measurement(
            measurement_name,
            group_letter,
            data,
            self.measurement_start or datetime.now(),
            self.measurement_end or datetime.now(),
            subterm,
            suffix,
        )

        return saved_path

    def save_measurement_manual(self, parent, group_letter: str, subterm: str = ""):
        """Manually save measurement via file dialog.

        Args:
            parent: Parent widget for dialog
            group_letter: Group identifier
            subterm: Subgroup term

        Returns:
            Path to saved file or None if cancelled/failed
        """
        data = self.get_csv_data()
        measurement_name = "Messung"

        if not data:
            MessageHelper.warning(
                parent,
                CONFIG["messages"]["no_data_to_save"],
                "Warnung",
            )
            return None

        if not measurement_name or not group_letter or not subterm:
            MessageHelper.warning(
                parent,
                CONFIG["messages"]["select_sample_and_group"],
                "Warnung",
            )
            return None

        saved_path = self.save_manager.manual_save_measurement(
            parent,
            measurement_name,
            group_letter,
            data,
            self.measurement_start or datetime.now(),
            self.measurement_end or datetime.now(),
            subterm,
        )

        return saved_path

    def has_unsaved_data(self) -> bool:
        """Check if there is unsaved measurement data."""
        return self.save_manager.has_unsaved()

    def mark_data_unsaved(self) -> None:
        """Mark current data as unsaved."""
        self.save_manager.mark_unsaved()

    def mark_data_saved(self) -> None:
        """Mark current data as saved."""
        self.save_manager.last_saved = True

    def set_auto_save(self, enabled: bool) -> None:
        """Enable or disable auto-save."""
        self.save_manager.auto_save = enabled

    def is_auto_save_enabled(self) -> bool:
        """Check if auto-save is enabled."""
        return self.save_manager.auto_save

    def set_measurement_times(self, start: datetime, end: datetime) -> None:
        """Set measurement start and end times."""
        self.measurement_start = start
        self.measurement_end = end
