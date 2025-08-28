# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QMainWindow,
    QVBoxLayout,
)
from PySide6.QtCore import QTimer  # pylint: disable=no-name-in-module
from src.device_manager import DeviceManager
from src.plot import PlotWidget
from src.debug_utils import Debug
from src.helper_classes import (
    import_config,
    Statusbar,
    SaveManager,
    MessageHelper,
)
from src.data_controller import DataController
from pyqt.ui_mainwindow import Ui_MainWindow
from datetime import datetime


# Import settings and messages
CONFIG = import_config()


class MainWindow(QMainWindow):
    """Main window of the HRNGGUI application.

    It handles the user interface, the device connection and the
    processing of the recorded data.  The implementation is split
    into several functional sections:

    1. Initialization and setup
    2. Data processing and statistics
    3. Measurement management
    4. UI event handlers
    5. Device control
    6. Helper functions
    """

    def __init__(self, device_manager: DeviceManager, parent=None):
        """Initialise the main window and all components.

        Args:
            device_manager: The connected device manager.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Measurement status
        self.is_measuring = False
        self.data_saved = True
        self.save_manager = SaveManager()
        self.measurement_start = None
        self.measurement_end = None
        self._elapsed_seconds = 0
        self._measurement_timer: QTimer | None = None

        # Initialize status bar for user feedback
        self.statusbar = Statusbar(self.ui.statusBar)
        self.statusbar.temp_message(CONFIG["messages"]["app_init"])

        # Initialise UI components first (plot needs to be created before device manager)
        self._setup_plot()
        self._setup_data_controller()
        self._setup_buttons()
        self._setup_timers()

        # Set up device manager after plot is created (acquisition thread runs continuously)
        self._setup_device_manager(device_manager)

        # Show success message (port attribute may not always be present)
        port = getattr(self.device_manager, "port", "device")
        self.statusbar.temp_message(
            CONFIG["messages"]["connected"].format(port),
            CONFIG["colors"]["green"],
        )

    #
    # 1. INITIALIZATION AND SETUP
    #

    def _setup_device_manager(self, device_manager: DeviceManager):
        """Configure the device manager and attach callbacks (multi-channel)."""
        self.device_manager = device_manager
        # Connect multi-channel callback; single value path kept unused
        self.device_manager.multi_callback = self.handle_multi_data
        self.device_manager.status_callback = self.statusbar.temp_message

        # Connect connection monitoring signals
        self.device_manager.connection_lost.connect(self._handle_connection_lost)
        self.device_manager.reconnection_attempt.connect(
            self._handle_reconnection_attempt
        )

        # Connect plot widget signal
        if hasattr(self, "plot_widget"):
            # Ensure acquisition thread is running (continuous mode)
            if not self.device_manager.acquire_thread:
                self.device_manager.start_acquisition()

            # Connect signals if thread is running
            if (
                self.device_manager.acquire_thread
                and self.device_manager.acquire_thread.isRunning()
            ):
                try:
                    self.device_manager.acquire_thread.multi_data_point.connect(
                        self.handle_multi_data
                    )
                    self.device_manager.acquire_thread.multi_data_point.connect(
                        self.plot_widget.on_new_point
                    )
                except Exception:  # pragma: no cover
                    pass
        else:
            # Fallback: start acquisition without plot connection
            if not self.device_manager.acquire_thread:
                self.device_manager.start_acquisition()
            else:
                try:
                    if self.device_manager.acquire_thread.isRunning():
                        self.device_manager.acquire_thread.multi_data_point.connect(
                            self.handle_multi_data
                        )
                except Exception:  # pragma: no cover
                    pass

    def _setup_plot(self):
        """Initialise the plot widgets (frequency & gyro Z over elapsed time)."""
        # Configuration for the two plots: frequency and gyro_z
        series_cfg = [
            {
                "name": "frequency",
                "y_index": 1,  # frequency is at index 1 in multi_data_point signal
                "title": "Frequency (Hz)",
            },
            {
                "name": "gyro_z",
                "y_index": 3,  # gyro_z is at index 3 in multi_data_point signal
                "title": "Gyroscope Z-Axis",
            },
        ]

        # Create the plot widget
        self.plot_widget = PlotWidget(
            series_cfg=series_cfg,
            max_plot_points=CONFIG["data_controller"]["max_history_size"],
        )

        # Add the plot widget to the UI layout
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.plot_widget)
        self.ui.plotWidget.setLayout(plot_layout)

    def _setup_data_controller(self):
        """Initialise the data controller (multi-channel)."""
        self.data_controller = DataController(
            frequency_plot=None,  # Plot handling is now done by PlotWidget
            gyroscope_plot=None,  # Plot handling is now done by PlotWidget
            display_widget=getattr(self.ui, "lcdNumber", None),
            table_widget=None,
            max_history=CONFIG["data_controller"]["max_history_size"],
        )

    def _setup_buttons(self):
        """Connect buttons to their respective callbacks."""
        # Connect measurement buttons
        self.ui.buttonStart.clicked.connect(self._start_measurement)
        self.ui.buttonStop.clicked.connect(self._stop_measurement)
        self.ui.buttonSave.clicked.connect(self._save_measurement)

        # Initial state of buttons
        self.ui.buttonStart.setEnabled(True)
        self.ui.buttonStop.setEnabled(False)
        self.ui.buttonSave.setEnabled(False)

        # Check auto-save setting
        self.ui.autoSave.setChecked(self.save_manager.auto_save)
        self.ui.autoSave.toggled.connect(self._change_auto_save)

    def _setup_timers(self):
        """Initialise timers (statistics and plot updates)."""
        Debug.debug("Setting up timers")

        # Statistics timer
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._update_statistics)
        self.stats_timer.start(CONFIG["timers"]["statistics_update_interval"])
        Debug.debug(
            f"Statistics timer started with interval: {CONFIG['timers']['statistics_update_interval']}ms"
        )

        # Plot update timer (100ms for smooth updates without lag)
        self.plot_update_timer = QTimer(self)
        self.plot_update_timer.timeout.connect(self._update_plots)
        self.plot_update_timer.start(100)  # 100ms = 10 FPS
        Debug.debug("Plot update timer started with 100ms interval")

    #
    # 2a. MEASUREMENT CONTROL
    #

    def _set_ui_measuring_state(self) -> None:
        """Put the UI into measurement mode."""
        self.ui.buttonStart.setEnabled(False)
        self.ui.buttonStop.setEnabled(True)
        self.ui.buttonSave.setEnabled(False)
        Debug.debug("UI switched to measuring mode")

    def _set_ui_idle_state(self) -> None:
        """Return the UI to idle mode after a measurement."""
        self.ui.buttonStart.setEnabled(True)
        self.ui.buttonStop.setEnabled(False)
        save_enabled = self.save_manager.has_unsaved()
        self.ui.buttonSave.setEnabled(save_enabled)
        Debug.debug(
            f"UI switched to idle mode (Save button: {'on' if save_enabled else 'off'})"
        )

    def _start_measurement(self):
        """Start measurement and adjust UI."""
        if self.save_manager.has_unsaved():
            if not MessageHelper.question(
                self,
                CONFIG["messages"]["unsaved_data"],
                "Warnung",
            ):
                return

        # Nur Export-Puffer leeren, Live-Plot Verlauf behalten
        self.data_controller.clear_storage_only()
        self.data_controller.start_recording()

        if self.device_manager.start_measurement():
            self.is_measuring = True
            self._set_ui_measuring_state()
            self.measurement_start = datetime.now()
            self._elapsed_seconds = 0

            # Add start marker to plot and enable auto-scroll
            if hasattr(self, "plot_widget") and self.data_controller.freq_series:
                # Use latest timestamp from data or 0 if no data yet
                latest_time = (
                    self.data_controller.freq_series[-1][0]
                    if self.data_controller.freq_series
                    else 0.0
                )
                self.plot_widget.add_measurement_marker(latest_time, is_start=True)
                self.plot_widget.set_auto_scroll(True)
                Debug.debug(f"Added START marker at time {latest_time}")

            self.statusbar.temp_message(
                CONFIG["messages"]["measurement_running"],
                CONFIG["colors"]["orange"],
            )

    def _stop_measurement(self):
        """Stop measurement and resume config polling."""
        self.device_manager.stop_measurement()
        # Aufzeichnung beenden (Plots laufen weiter live)
        self.data_controller.stop_recording()
        self.is_measuring = False
        self.measurement_end = datetime.now()

        # Add stop marker to plot and disable auto-scroll
        if hasattr(self, "plot_widget") and self.data_controller.freq_series:
            # Use latest timestamp from data
            latest_time = (
                self.data_controller.freq_series[-1][0]
                if self.data_controller.freq_series
                else 0.0
            )
            self.plot_widget.add_measurement_marker(latest_time, is_start=False)
            self.plot_widget.set_auto_scroll(False)
            Debug.debug(f"Added STOP marker at time {latest_time}")

        self._set_ui_idle_state()
        self.statusbar.temp_message(
            CONFIG["messages"]["measurement_stopped"],
            CONFIG["colors"]["red"],
        )
        if self.save_manager.auto_save and not self.save_manager.last_saved:
            data = self.data_controller.get_csv_data()
            group_letter = self.ui.groupLetter.currentText()
            suffix = self.ui.suffix.text().strip()
            rad_sample = "MEAS"  # simplified placeholder (no separate sample selection)
            saved_path = self.save_manager.auto_save_measurement(
                rad_sample,
                group_letter,
                data,
                self.measurement_start or datetime.now(),
                self.measurement_end or datetime.now(),
                suffix,
            )
            if saved_path and saved_path.exists():
                self.data_saved = True
                self.ui.buttonSave.setEnabled(False)
                self.statusbar.temp_message(
                    f"Messung erfolgreich gespeichert: {saved_path}",
                    CONFIG["colors"]["green"],
                )
                Debug.info(f"Messung automatisch gespeichert: {saved_path}")
            else:
                MessageHelper.error(
                    self,
                    "Fehler beim Speichern der Messung. Siehe Log für Details.",
                    "Fehler",
                )

    def _save_measurement(self):
        """Manually save the current measurement data using a file dialog."""
        try:
            # Check if there is data to save
            if not self.save_manager.has_unsaved():
                MessageHelper.info(
                    self,
                    "Keine ungespeicherten Daten vorhanden.",
                    "Information",
                )
                return

            data = self.data_controller.get_csv_data()
            rad_sample = "MEAS"
            group_letter = self.ui.groupLetter.currentText()

            saved_path = self.save_manager.manual_save_measurement(
                self,
                rad_sample,
                group_letter,
                data,
                self.measurement_start or datetime.now(),
                self.measurement_end or datetime.now(),
            )

            if saved_path and saved_path.exists():
                self.data_saved = True
                self.ui.buttonSave.setEnabled(False)
                self.statusbar.temp_message(
                    f"Messung erfolgreich gespeichert: {saved_path}",
                    CONFIG["colors"]["green"],
                )
                Debug.info(f"Messung manuell gespeichert: {saved_path}")
            else:
                MessageHelper.error(
                    self,
                    "Fehler beim Speichern der Messung. Siehe Log für Details.",
                    "Fehler",
                )

        except Exception as e:
            Debug.error(f"Fehler beim manuellen Speichern: {e}")
            MessageHelper.error(
                self,
                f"Unerwarteter Fehler beim Speichern: {str(e)}",
                "Fehler",
            )

    #
    # 2. DATA PROCESSING AND STATISTICS
    #

    def handle_multi_data(
        self, elapsed_s: float, freq: float, accel_z: float, gyro_z: float
    ):
        """Handle incoming multi-channel data.

        Updates plots & table via DataController. Mark data unsaved if a
        measurement session is active (saving toggled by start/stop buttons).
        """
        self.data_controller.handle_multi_data_point(elapsed_s, freq, accel_z, gyro_z)

        # Update primary LCD display (frequency preferred, else gyro)
        display_value = (
            freq if not (freq is None or freq != freq) else gyro_z
        )  # NaN check
        lcd = getattr(self.ui, "lcdNumber", None)
        if lcd:
            try:
                lcd.display(display_value if display_value == display_value else 0)
            except Exception:  # pragma: no cover
                pass
        # Update count LCD if available
        lcd_count = getattr(self.ui, "lcdNumber_2", None)
        if lcd_count:
            try:
                lcd_count.display(len(self.data_controller.data_points))
            except Exception:  # pragma: no cover
                pass

        if self.is_measuring:
            self.data_saved = False
            self.save_manager.mark_unsaved()
        else:
            # If idle, allow user to save accumulated data
            if self.save_manager.has_unsaved():
                self.ui.buttonSave.setEnabled(True)

    def _update_statistics(self):
        """Update basic frequency statistics (Hz)."""
        stats = self.data_controller.get_statistics()
        if stats["count"] > 0 and self.is_measuring:
            stats_text = (
                f"Points: {int(stats['count'])} | "
                f"Min: {stats['min']:.1f} Hz | "
                f"Max: {stats['max']:.1f} Hz | "
                f"Avg: {stats['avg']:.1f} Hz"
            )
            if stats["count"] > 1:
                stats_text += f" | σ: {stats['stdev']:.1f}"
            self.statusbar.temp_message(
                CONFIG["messages"]["measurement_running"] + "  " + stats_text,
                CONFIG["colors"]["orange"],
            )

    def _update_plots(self):
        """Update the plot widget with queued data and LCD displays."""
        Debug.debug("_update_plots called")

        # Update plots
        if hasattr(self, "plot_widget"):
            self.plot_widget.update_plots()
            Debug.debug("Plot widget updated")
        else:
            Debug.debug("Plot widget not available")

        # Update LCD displays with current values
        self._update_lcd_displays()

    def _update_lcd_displays(self):
        """Update LCD displays with current data values."""
        Debug.debug("_update_lcd_displays called")

        if not hasattr(self, "data_controller"):
            Debug.debug("DataController not available")
            return

        try:
            # Get current values from data controller
            current_values = self.data_controller.get_current_values()
            Debug.debug(f"Current values from data_controller: {current_values}")

            # Update cDataPoints (total number of data points)
            if hasattr(self.ui, "cDataPoints"):
                self.ui.cDataPoints.display(current_values["data_points_count"])
                Debug.debug(
                    f"Updated cDataPoints: {current_values['data_points_count']}"
                )
            else:
                Debug.debug("cDataPoints widget not found")

            # Update cFrequency (current frequency)
            if hasattr(self.ui, "cFrequency"):
                self.ui.cFrequency.display(current_values["current_frequency"])
                Debug.debug(
                    f"Updated cFrequency: {current_values['current_frequency']}"
                )
            else:
                Debug.debug("cFrequency widget not found")

            # Update cZGyro (current gyro Z value)
            if hasattr(self.ui, "cZGyro"):
                self.ui.cZGyro.display(current_values["current_gyro_z"])
                Debug.debug(f"Updated cZGyro: {current_values['current_gyro_z']}")
            else:
                Debug.debug("cZGyro widget not found")

        except Exception as e:  # pragma: no cover
            Debug.error(f"Fehler beim Aktualisieren der LCD-Displays: {e}")

    # _update_progress removed (legacy progress bar no longer in UI)

    #
    # 3. DEVICE CONTROL
    #

    # Legacy GM counter UI elements removed: _update_control_display / _apply_settings
    # (Controls like voltage, counting_time no longer polled.)

    def _change_auto_save(self, checked: bool) -> None:
        """Handle a change of the auto-save option.

        Args:
            checked: ``True`` if auto save is enabled.
        """
        self.save_manager.auto_save = checked
        if checked:
            self.statusbar.temp_message(
                CONFIG["messages"]["auto_save_enabled"],
                CONFIG["colors"]["green"],
                1000,
            )
        else:
            self.statusbar.temp_message(
                CONFIG["messages"]["auto_save_disabled"],
                CONFIG["colors"]["green"],
                1000,
            )

    def closeEvent(self, event):
        """Handle the window close event and shut down all components cleanly.

        Args:
            event: The close event from Qt.
        """
        Debug.info("Anwendung wird geschlossen, fahre Komponenten herunter...")

        # Stop data acquisition in the DeviceManager
        if hasattr(self, "device_manager"):
            Debug.info("Stoppe Datenerfassung...")
            self.device_manager.stop_acquisition()
            if hasattr(self.device_manager, "device") and self.device_manager.device:
                Debug.info("Schließe Geräteverbindung...")
                self.device_manager.device.close()

        # Stop active timers
        for timer_attr in ["stats_timer", "plot_update_timer"]:
            if hasattr(self, timer_attr):
                timer = getattr(self, timer_attr)
                if timer.isActive():
                    Debug.debug(f"Stoppe Timer: {timer_attr}")
                    timer.stop()

        # Stop the DataController GUI update timer
        if hasattr(self, "data_controller"):
            Debug.info("DataController Cleanup...")

        # Pass event to base class
        Debug.info("Anwendung wird geschlossen")
        if event:
            event.accept()

    def _handle_connection_lost(self) -> None:
        """Handle connection loss signal from device manager."""
        Debug.info("Connection lost detected in main window")
        # Update UI to show connection lost state
        self.statusbar.temp_message(
            "Connection lost - attempting reconnection...", "red"
        )
        # Optionally disable measurement controls while reconnecting
        if hasattr(self, "ui"):
            # You could disable buttons here if needed
            pass

    def _handle_reconnection_attempt(self, attempt_number: int) -> None:
        """Handle reconnection attempt signal from device manager."""
        Debug.info(f"Reconnection attempt {attempt_number}")
        self.statusbar.temp_message(
            f"Reconnecting... (attempt {attempt_number})", "orange"
        )
