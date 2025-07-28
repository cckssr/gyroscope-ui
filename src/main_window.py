# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QMainWindow,
    QVBoxLayout,
    QCompleter,
)
from PySide6.QtCore import QTimer, Qt  # pylint: disable=no-name-in-module
from src.device_manager import DeviceManager
from src.control import ControlWidget
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

        # Set up device manager
        self._setup_device_manager(device_manager)

        # Initialise UI components
        self._setup_plot()
        self._setup_data_controller()
        self._setup_controls()
        self._setup_buttons()
        self._setup_radioactive_sample_input()
        self._setup_timers()

        # Initial update of the UI
        self._update_control_display()

        # Show success message
        self.statusbar.temp_message(
            CONFIG["messages"]["connected"].format(self.device_manager.port),
            CONFIG["colors"]["green"],
        )

    #
    # 1. INITIALIZATION AND SETUP
    #

    def _setup_device_manager(self, device_manager: DeviceManager):
        """Configure the device manager and attach callbacks.

        Args:
            device_manager: The device manager instance to use.
        """
        self.device_manager = device_manager
        self.device_manager.data_callback = self.handle_data
        self.device_manager.status_callback = self.statusbar.temp_message

        # Ensure the acquisition thread forwards data to this window. When the
        # connection dialog created the DeviceManager the acquisition thread may
        # already be running without our callback connected.
        self.device_manager.start_acquisition()

    def _setup_controls(self):
        self.control = ControlWidget(
            device_manager=self.device_manager,
        )

    def _setup_plot(self):
        """Initialise the plot widget."""
        self.plot = PlotWidget(
            max_plot_points=CONFIG["plot"]["max_points"],
            width=self.ui.timePlot.width(),
            height=self.ui.timePlot.height(),
            dpi=self.logicalDpiX(),
            fontsize=self.ui.timePlot.fontInfo().pixelSize(),
            xlabel=CONFIG["plot"]["x_label"],
            ylabel=CONFIG["plot"]["y_label"],
        )
        QVBoxLayout(self.ui.timePlot).addWidget(self.plot)

    def _setup_data_controller(self):
        """Initialise the data controller."""
        self.data_controller = DataController(
            plot_widget=self.plot,
            display_widget=self.ui.currentCount,
            max_history=CONFIG["data_controller"]["max_history_size"],
            gui_update_interval=CONFIG["timers"]["gui_update_interval"],
        )

    def _setup_buttons(self):
        """Connect buttons to their respective callbacks."""
        # Connect measurement buttons
        self.ui.buttonStart.clicked.connect(self._start_measurement)
        self.ui.buttonStop.clicked.connect(self._stop_measurement)
        self.ui.buttonSave.clicked.connect(self._save_measurement)
        self.ui.buttonSetting.clicked.connect(self._apply_settings)

        # Initial state of buttons
        self.ui.buttonStart.setEnabled(True)
        self.ui.buttonStop.setEnabled(False)
        self.ui.buttonSave.setEnabled(False)

        # Check auto-save setting
        self.ui.autoSave.setChecked(self.save_manager.auto_save)
        self.ui.autoSave.toggled.connect(self._change_auto_save)

    def _setup_radioactive_sample_input(self):
        """Initialise the input field for radioactive samples."""
        samples = CONFIG["radioactive_samples"]
        radCombo = self.ui.radSample
        radCombo.clear()
        radCombo.addItems(samples)
        Debug.debug(
            f"Radioaktive Proben geladen: {len(samples)} Proben",
        )
        radCombo.setCurrentIndex(-1)  # No default selection

        # QCompleter for radioactive samples
        completer = QCompleter(samples)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        radCombo.setCompleter(completer)

    def _setup_timers(self):
        """Initialise timers used by the application.

        Measurement data are acquired in the background by ``DeviceManager``
        while configuration polling happens only when no measurement is running.
        This keeps the acquisition loop free of ``sleep`` calls and the GUI
        responsive.
        """
        # Timer for control updates
        self.control_update_timer = QTimer(self)
        self.control_update_timer.timeout.connect(self._update_control_display)
        self.control_update_timer.start(CONFIG["timers"]["control_update_interval"])

        # Timer for statistics updates (UI only)
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._update_statistics)
        self.stats_timer.start(CONFIG["timers"]["statistics_update_interval"])

    #
    # 2a. MEASUREMENT CONTROL
    #

    def _set_ui_measuring_state(self) -> None:
        """Put the UI into measurement mode."""
        self.control_update_timer.stop()
        self.ui.buttonStart.setEnabled(False)
        self.ui.buttonSetting.setEnabled(False)
        self.ui.buttonStop.setEnabled(True)
        self.ui.buttonSave.setEnabled(False)
        Debug.debug("UI in Messmodus gesetzt")

    def _set_ui_idle_state(self) -> None:
        """Return the UI to idle mode after a measurement."""
        self.control_update_timer.start(CONFIG["timers"]["control_update_interval"])
        self.ui.buttonStart.setEnabled(True)
        self.ui.buttonSetting.setEnabled(True)
        self.ui.buttonStop.setEnabled(False)
        # buttonSave is enabled separately based on existing data
        save_enabled = self.save_manager.has_unsaved()
        self.ui.buttonSave.setEnabled(save_enabled)
        Debug.debug(
            f"UI in Ruhemodus gesetzt (Save-Button: {'aktiviert' if save_enabled else 'deaktiviert'})"
        )

    def _setup_progress_bar(self, duration_seconds: int) -> None:
        """Configure the progress bar for the given duration.

        Args:
            duration_seconds: Duration in seconds (``999`` means infinite).
        """
        if duration_seconds != 999:
            # Finite duration - progress bar with timer
            self.ui.progressBar.setMaximum(duration_seconds)
            self.ui.progressBar.setValue(0)
            self._measurement_timer = QTimer(self)
            self._measurement_timer.timeout.connect(self._update_progress)
            self._measurement_timer.start(1000)  # Update every second
            Debug.debug(f"ProgressBar konfiguriert für {duration_seconds} Sekunden")
        else:
            # Infinite duration - indeterminate progress bar
            self.ui.progressBar.setMaximum(0)
            self.ui.progressBar.setValue(0)
            self._measurement_timer = None
            Debug.debug("ProgressBar konfiguriert für unendliche Messdauer")

    def _stop_progress_bar(self) -> None:
        """Stop the progress bar and its timer."""
        if self._measurement_timer:
            self._measurement_timer.stop()
            self._measurement_timer = None

        # Reset progress bar to idle state
        self.ui.progressBar.setMaximum(100)
        self.ui.progressBar.setValue(0)
        self._elapsed_seconds = 0
        Debug.debug("ProgressBar gestoppt und zurückgesetzt")

    def _start_measurement(self):
        """Start measurement and adjust UI."""
        if self.save_manager.has_unsaved():
            if not MessageHelper.question(
                self,
                CONFIG["messages"]["unsaved_data"],
                "Warnung",
            ):
                return

        self.data_controller.clear_data()

        if self.device_manager.start_measurement():
            self.is_measuring = True
            self._set_ui_measuring_state()
            self.measurement_start = datetime.now()
            self._elapsed_seconds = 0
            seconds = int(self.ui.cDuration.value())
            if seconds == 0:
                seconds = 999
            self._setup_progress_bar(seconds)
            self.statusbar.temp_message(
                CONFIG["messages"]["measurement_running"],
                CONFIG["colors"]["orange"],
            )

    def _stop_measurement(self):
        """Stop measurement and resume config polling."""
        self.device_manager.stop_measurement()
        self.is_measuring = False
        self.measurement_end = datetime.now()
        self._stop_progress_bar()
        self._set_ui_idle_state()
        self.statusbar.temp_message(
            CONFIG["messages"]["measurement_stopped"],
            CONFIG["colors"]["red"],
        )
        if self.save_manager.auto_save and not self.save_manager.last_saved:
            data = self.data_controller.get_csv_data()
            rad_sample = self.ui.radSample.currentText()
            group_letter = self.ui.groupLetter.currentText()
            suffix = self.ui.suffix.text().strip()
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
            rad_sample = self.ui.radSample.currentText()
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

    def handle_data(self, index, value):
        """Handle incoming data from the device.

        The values are forwarded to ``DataController`` using the fast
        queue-based API.

        Args:
            index: Index of the data point.
            value: Measured value.
        """
        # Use the fast queue-based method for better performance
        self.data_controller.add_data_point_fast(index, value)

        # Mark data as unsaved
        self.data_saved = False
        self.save_manager.mark_unsaved()

        # Enable save button when not measuring (idle)
        if not self.is_measuring:
            self.ui.buttonSave.setEnabled(True)

        # Statistics are now updated every 2s using their own timer
        # No manual update necessary - better performance

    def _update_statistics(self):
        """Update statistics shown in the user interface."""
        try:
            # Retrieve statistics from DataController
            stats = self.data_controller.get_statistics()

            # Only update when data points are available
            if stats["count"] > 0:
                stats_text = (
                    f"Datenpunkte: {int(stats['count'])} | "
                    f"Min: {stats['min']:.0f} µs | "
                    f"Max: {stats['max']:.0f} µs | "
                    f"Mittelwert: {stats['avg']:.0f} µs"
                )

                # Add standard deviation when enough data points are present
                if stats["count"] > 1:
                    stats_text += f" | σ: {stats['stdev']:.0f} µs"

                # Temporarily update status bar while a measurement is running
                if self.is_measuring:
                    self.statusbar.temp_message(
                        CONFIG["messages"]["measurement_running"] + "\t" + stats_text,
                        CONFIG["colors"]["orange"],
                    )

        except Exception as e:
            Debug.error(
                f"Fehler beim Aktualisieren der Statistiken: {e}", exc_info=True
            )

    def _update_progress(self) -> None:
        """Update progress bar during finite measurements."""

        self._elapsed_seconds += 1
        self.ui.progressBar.setValue(self._elapsed_seconds)
        if (
            self.ui.progressBar.maximum() > 0
            and self._elapsed_seconds >= self.ui.progressBar.maximum()
        ):
            self._stop_measurement()

    #
    # 3. DEVICE CONTROL
    #

    def _update_control_display(self):
        """Update the displayed configuration values from the GM counter."""
        try:
            # Request fresh data from the GM counter
            data = self.control.get_settings()
            if not data:
                Debug.error("Keine Daten vom GM-Counter erhalten.")
                return

            # Update UI elements
            label = CONFIG["gm_counter"]["label_map"]

            self.ui.currentCount.display(data["count"])
            self.ui.lastCount.display(
                data["last_count"]
            )  # TODO: last_count implementieren mit check

            self.ui.cVoltage.display(data["voltage"])
            self.ui.cDuration.display(data["counting_time"])
            self.ui.cMode.setText(
                label["repeat_on"] if data["repeat"] else label["repeat_off"]
            )
            # self.ui.cQueryMode.setText(label["auto_on"] if data["auto_query"] else label["auto_off"]) # FEAT: auto_query implementieren

        except Exception as e:
            Debug.error(f"Fehler bei der Aktualisierung der Anzeige: {e}")

    def _apply_settings(self):
        """
        Applies the current settings from the UI to the GM-Counter.
        """
        try:
            settings = {
                "voltage": int(self.ui.sVoltage.value()),
                "counting_time": int(self.ui.sDuration.currentIndex()),
                "repeat": self.ui.cMode.text() == "Repeat On",
                # "auto_query": self.ui.cQueryMode.text() == "Auto On",
            }
            self.control.apply_settings(settings)
            self.statusbar.temp_message(
                CONFIG["messages"]["settings_applied"],
                CONFIG["colors"]["green"],
            )
            Debug.info(
                "Einstellungen erfolgreich angewendet: " + str(settings.values())
            )
        except Exception as e:
            Debug.error(f"Fehler beim Anwenden der Einstellungen: {e}")

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
            try:
                Debug.info("Stoppe Datenerfassung...")
                self.device_manager.stop_acquisition()

                # Close the connection if a real device is connected
                if (
                    hasattr(self.device_manager, "device")
                    and self.device_manager.device
                ):
                    Debug.info("Schließe Geräteverbindung...")
                    self.device_manager.device.close()
            except Exception as e:
                Debug.error(f"Fehler beim Herunterfahren des DeviceManagers: {e}")

        # Stop all timers
        for timer_attr in ["control_update_timer", "stats_timer"]:
            if hasattr(self, timer_attr):
                timer = getattr(self, timer_attr)
                if timer.isActive():
                    Debug.debug(f"Stoppe Timer: {timer_attr}")
                    timer.stop()

        # Stop the DataController GUI update timer
        if hasattr(self, "data_controller"):
            try:
                Debug.info("Stoppe DataController GUI-Updates...")
                self.data_controller.stop_gui_updates()
            except Exception as e:
                Debug.error(f"Fehler beim Stoppen der DataController GUI-Updates: {e}")

        # Pass event to base class
        Debug.info("Anwendung wird geschlossen")
        event.accept()
