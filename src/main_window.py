# -*- coding: utf-8 -*-
from datetime import datetime
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QMainWindow,
    QVBoxLayout,
    QApplication,
    QWidget,
)
from PySide6.QtCore import QTimer  # pylint: disable=no-name-in-module
from PySide6.QtGui import QPalette

# Relative imports für installiertes Package, absolute für lokale Ausführung
try:
    from .device_manager import DeviceManager
    from .plot import PlotWidget
    from .debug_utils import Debug
    from .helper_classes import (
        import_config,
        Statusbar,
        MessageHelper,
    )
    from .data_controller import DataController
    from .pyqt.ui_mainwindow import Ui_MainWindow
except ImportError:
    from device_manager import DeviceManager
    from plot import PlotWidget
    from debug_utils import Debug
    from helper_classes import (
        import_config,
        Statusbar,
        MessageHelper,
    )
    from data_controller import DataController
    from pyqt.ui_mainwindow import Ui_MainWindow


# Import settings and messages
CONFIG = import_config()


class MainWindow(QMainWindow):
    """Main window of the Gyroscope application.

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
        self.data_clear_flag = True  # Flag to prevent data overwrite
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
                "x_label": CONFIG["plot"]["frequency"]["x_label"],
                "y_label": CONFIG["plot"]["frequency"]["y_label"],
            },
            {
                "name": "gyro_z",
                "y_index": 3,  # gyro_z is at index 3 in multi_data_point signal
                "title": "Gyroscope Z-Axis",
                "x_label": CONFIG["plot"]["acceleration"]["x_label"],
                "y_label": CONFIG["plot"]["acceleration"]["y_label"],
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

        # Apply system theme colors to plots
        self._apply_system_theme_to_plots()

        # Plot widget is always visible, but data updates are controlled by measurement state

    def _apply_system_theme_to_plots(self):
        """Apply system theme colors to the plot widget."""
        try:
            app = QApplication.instance()
            if app is None:
                return

            # Get a widget to access the palette
            widget = QWidget()
            palette = widget.palette()

            # Get system colors
            bg_color = palette.color(QPalette.ColorRole.Window)
            text_color = palette.color(QPalette.ColorRole.WindowText)
            base_color = palette.color(QPalette.ColorRole.Base)

            # Convert to RGB tuples and hex string for pyqtgraph
            bg_rgb = (bg_color.red(), bg_color.green(), bg_color.blue())
            text_rgb = (text_color.red(), text_color.green(), text_color.blue())
            base_hex = base_color.name()

            # Apply colors to plot widget
            self.plot_widget.apply_theme_colors(
                bg_color=bg_rgb, text_color=text_rgb, base_color=base_hex
            )

        except Exception as e:
            Debug.error(f"Failed to apply system theme to plots: {e}")

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
        self.ui.buttonReset.clicked.connect(self._reset_measurement)

        # Initial state of buttons
        self.ui.buttonStart.setEnabled(
            True
        )  # Will be updated by _update_start_button_state
        self.ui.buttonStop.setEnabled(False)
        self.ui.buttonSave.setEnabled(False)
        self.ui.buttonReset.setEnabled(False)

        # Update start button based on clear flag
        self._update_start_button_state()

        # Check auto-save setting
        self.ui.autoSave.setChecked(self.data_controller.is_auto_save_enabled())
        self.ui.autoSave.toggled.connect(self._change_auto_save)

    def _setup_timers(self):
        """Initialise timers (plot updates only)."""
        Debug.debug("Setting up timers")

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
        self.ui.buttonReset.setEnabled(False)
        Debug.debug("UI switched to measuring mode")

    def _set_ui_idle_state(self) -> None:
        """Return the UI to idle mode after a measurement."""
        self._update_start_button_state()
        self.ui.buttonStop.setEnabled(False)
        save_enabled = self.data_controller.has_unsaved_data()
        self.ui.buttonSave.setEnabled(save_enabled)
        self.ui.buttonReset.setEnabled(save_enabled)
        Debug.debug(
            f"UI switched to idle mode (Save: {'on' if save_enabled else 'off'}, Reset: {'on' if save_enabled else 'off'})"
        )

    def _start_measurement(self):
        """Start measurement and adjust UI."""
        # Check if clear flag is set (prevents accidental data overwrite)
        if not self.data_clear_flag:
            Debug.info("Start abgelehnt: Clear flag nicht gesetzt")
            return

        if self.data_controller.has_unsaved_data():
            if not MessageHelper.question(
                self,
                CONFIG["messages"]["unsaved_data"],
                "Warnung",
            ):
                return

        # Nur Export-Puffer leeren, Live-Plot Verlauf behalten
        self.data_controller.clear_storage_only()
        self.data_controller.start_recording()
        self.data_clear_flag = False  # Reset flag after starting

        if self.device_manager.start_measurement():
            self.is_measuring = True
            self._set_ui_measuring_state()
            measurement_start = datetime.now()
            self._elapsed_seconds = 0
            self.data_controller.set_measurement_times(
                measurement_start, measurement_start
            )

            # Enable plot data updates and clear old data for new measurement
            if hasattr(self, "plot_widget"):
                self.plot_widget.set_measurement_mode(True)
                self.plot_widget.set_auto_scroll(True)
                Debug.debug(
                    "Plot widget enabled for measurement data updates and cleared"
                )

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
        measurement_end = datetime.now()
        self.data_controller.set_measurement_times(
            self.data_controller.measurement_start or measurement_end, measurement_end
        )

        # Disable plot data updates and auto-scroll
        if hasattr(self, "plot_widget"):
            self.plot_widget.set_measurement_mode(False)
            self.plot_widget.set_auto_scroll(False)
            Debug.debug("Plot widget disabled for measurement data updates")

        self._set_ui_idle_state()
        self.statusbar.temp_message(
            CONFIG["messages"]["measurement_stopped"],
            CONFIG["colors"]["red"],
        )

        # Auto-save if enabled
        group_letter = self.ui.groupLetter.currentText()
        suffix = self.ui.suffix.text().strip()
        saved_path = self.data_controller.save_measurement_auto(group_letter, suffix)

        if saved_path and saved_path.exists():
            self.data_clear_flag = True  # Set clear flag after successful save
            self.ui.buttonSave.setEnabled(False)
            self.ui.buttonReset.setEnabled(False)
            self._update_start_button_state()
            self.statusbar.temp_message(
                CONFIG["messages"]["data_saved"].format(saved_path),
                CONFIG["colors"]["green"],
            )
            Debug.info(f"Messung automatisch gespeichert: {saved_path}")
        elif saved_path is not None:  # Attempted to save but failed
            MessageHelper.error(
                self,
                CONFIG["messages"]["save_error"].format(saved_path),
                "Fehler",
            )

    def _save_measurement(self):
        """Manually save the current measurement data using a file dialog."""
        try:
            # Check if there is data to save
            if not self.data_controller.has_unsaved_data():
                MessageHelper.info(
                    self,
                    CONFIG["messages"]["no_data"],
                    "Information",
                )
                return

            group_letter = self.ui.groupLetter.currentText()
            saved_path = self.data_controller.save_measurement_manual(
                self, group_letter
            )

            if saved_path and saved_path.exists():
                self.data_clear_flag = True  # Set clear flag after successful save
                self.ui.buttonSave.setEnabled(False)
                self.ui.buttonReset.setEnabled(False)
                self._update_start_button_state()
                self.statusbar.temp_message(
                    CONFIG["messages"]["data_saved"].format(saved_path),
                    CONFIG["colors"]["green"],
                )
                Debug.info(f"Messung manuell gespeichert: {saved_path}")
            elif saved_path is None:
                # User cancelled or validation failed - do nothing
                pass
            else:
                MessageHelper.error(
                    self,
                    CONFIG["messages"]["save_error"].format(saved_path),
                    "Fehler",
                )

        except Exception as e:
            Debug.error(f"Fehler beim manuellen Speichern: {e}")
            MessageHelper.error(
                self,
                CONFIG["messages"]["save_error"].format(e),
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
            self.data_controller.mark_data_unsaved()
        else:
            # If idle, allow user to save accumulated data
            if self.data_controller.has_unsaved_data():
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
        """Update the plot widget (only update curves during measurement) and LCD displays."""
        Debug.debug("_update_plots called")

        # Always update plot widget (data processing), but curves only during measurement
        if hasattr(self, "plot_widget"):
            self.plot_widget.update_plots()
            Debug.debug("Plot widget updated")
        else:
            Debug.debug("Plot widget not available")

        # Always update LCD displays (regardless of measurement state)
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
        self.data_controller.set_auto_save(checked)
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

    def _reset_measurement(self) -> None:
        """Reset measurement data and plots. Sets clear flag to allow new measurement."""
        try:
            # Clear all data in data controller
            self.data_controller.clear_data()

            # Clear plots
            if hasattr(self, "plot_widget"):
                self.plot_widget.clear_plot_data()
                Debug.debug("Plot widget cleared")

            # Reset save manager
            self.data_controller.mark_data_saved()

            # Set clear flag to allow new measurement
            self.data_clear_flag = True

            # Update UI state
            self.ui.buttonSave.setEnabled(False)
            self.ui.buttonReset.setEnabled(False)
            self._update_start_button_state()

            # Show success message
            self.statusbar.temp_message(
                CONFIG["messages"]["data_reset"],
                CONFIG["colors"]["green"],
            )
            Debug.info("Messdaten zurückgesetzt und Plot geleert")

        except Exception as e:
            Debug.error(f"Fehler beim Zurücksetzen der Messdaten: {e}")
            MessageHelper.error(
                self,
                f"Fehler beim Zurücksetzen: {e}",
                "Fehler",
            )

    def _update_start_button_state(self) -> None:
        """Update the start button state based on clear flag."""
        self.ui.buttonStart.setEnabled(self.data_clear_flag)
        Debug.debug(
            f"Start button {'enabled' if self.data_clear_flag else 'disabled'} (clear_flag={self.data_clear_flag})"
        )

    def closeEvent(self, event):
        """Handle the window close event and shut down all components cleanly.

        Args:
            event: The close event from Qt.
        """
        Debug.info("Anwendung wird geschlossen, fahre Komponenten herunter...")

        # Check for unsaved data before closing
        if hasattr(self, "data_controller") and self.data_controller.has_unsaved_data():
            # Ask user if they want to save
            response = MessageHelper.question(
                self,
                CONFIG["messages"]["close_unsaved_data_question"],
                CONFIG["messages"]["close_unsaved_data_title"],
            )
            if response:  # User clicked "Yes" - wants to save
                # Trigger save dialog
                self._save_measurement()
                # Check if save was successful or if there's still unsaved data
                if self.data_controller.has_unsaved_data():
                    # Save was not successful (cancelled, validation failed, or error)
                    # Don't close - let user fix the issue or explicitly choose to close without saving
                    Debug.info("Speicherung nicht erfolgreich - Schließen abgebrochen")
                    event.ignore()
                    return
            else:
                # User clicked "No" - wants to close without saving
                # Ask for confirmation since data will be lost
                confirm_close = MessageHelper.question(
                    self,
                    CONFIG["messages"]["close_after_cancel_question"],
                    CONFIG["messages"]["close_after_cancel_title"],
                )
                if not confirm_close:  # User doesn't want to close after all
                    event.ignore()
                    return

        # Stop data acquisition in the DeviceManager
        if hasattr(self, "device_manager"):
            Debug.info("Stoppe Datenerfassung...")
            self.device_manager.stop_acquisition()
            if hasattr(self.device_manager, "device") and self.device_manager.device:
                Debug.info("Schließe Geräteverbindung...")
                self.device_manager.device.close()

        # Stop active timers
        for timer_attr in ["plot_update_timer"]:
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
        self.statusbar.temp_message(CONFIG["messages"]["disconnected"], "red")
        # Optionally disable measurement controls while reconnecting
        if hasattr(self, "ui"):
            # You could disable buttons here if needed
            pass

    def _handle_reconnection_attempt(self, attempt_number: int) -> None:
        """Handle reconnection attempt signal from device manager."""
        Debug.info(f"Reconnection attempt {attempt_number}")
        self.statusbar.temp_message(
            CONFIG["messages"]["connecting"].format(attempt_number), "orange"
        )
