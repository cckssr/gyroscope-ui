# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QMainWindow,
    QVBoxLayout,
    QCompleter,
)
from PySide6.QtCore import QTimer, Qt  # pylint: disable=no-name-in-module
from src.device_manager import DeviceManager
from src.control import ControlWidget
from src.plot import PlotWidget, HistogramWidget
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
        """
        Initialisiert das Hauptfenster und alle Komponenten der Anwendung.

        Args:
            device_manager (DeviceManager): Der verbundene Geräte-Manager
            parent: Das übergeordnete Widget (optional)
        """
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Status der Messung
        self.is_measuring = False
        self.data_saved = True
        self.save_manager = SaveManager()
        self.measurement_start = None
        self.measurement_end = None
        self._elapsed_seconds = 0
        self._measurement_timer: QTimer | None = None

        # Statusleiste für Feedback initialisieren
        self.statusbar = Statusbar(self.ui.statusBar)
        self.statusbar.temp_message(CONFIG["messages"]["app_init"])

        # Geräte-Manager einrichten
        self._setup_device_manager(device_manager)

        # UI-Komponenten initialisieren
        self._setup_plot()
        self._setup_data_controller()
        self._setup_controls()
        self._setup_buttons()
        self._setup_radioactive_sample_input()
        self._setup_timers()

        # # Erste Aktualisierung der UI
        self._update_control_display()

        # Erfolgsmeldung anzeigen
        self.statusbar.temp_message(
            CONFIG["messages"]["connected"].format(self.device_manager.port),
            CONFIG["colors"]["green"],
        )

    #
    # 1. INITIALISIERUNG UND SETUP
    #

    def _setup_device_manager(self, device_manager: DeviceManager):
        """
        Initialisiert den Geräte-Manager und setzt Callbacks für Daten- und Statusaktualisierungen.

        Args:
            device_manager (DeviceManager): Der zu verwendende Geräte-Manager
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
        """
        Richtet das Plot-Widget ein.
        """
        self.plot = PlotWidget(
            max_plot_points=CONFIG["plot"]["max_points"],
            fontsize=self.ui.timePlot.fontInfo().pixelSize(),
            xlabel=CONFIG["plot"]["x_label"],
            ylabel=CONFIG["plot"]["y_label"],
        )
        QVBoxLayout(self.ui.timePlot).addWidget(self.plot)

        # Histogram plot
        self.histogram = HistogramWidget()
        QVBoxLayout(self.ui.histogramm).addWidget(self.histogram)

    def _setup_data_controller(self):
        """
        Richtet den Daten-Controller ein.
        """
        self.data_controller = DataController(
            plot_widget=self.plot,
            display_widget=self.ui.currentCount,
            table_widget=self.ui.tableView,
            max_history=CONFIG["data_controller"]["max_history_size"],
        )

    def _setup_buttons(self):
        """
        Verbindet die Schaltflächen mit ihren jeweiligen Funktionen.
        """
        # Mess-Steuerungsschaltflächen verbinden
        self.ui.buttonStart.clicked.connect(self._start_measurement)
        self.ui.buttonStop.clicked.connect(self._stop_measurement)
        self.ui.buttonSave.clicked.connect(self._save_measurement)
        self.ui.buttonSetting.clicked.connect(self._apply_settings)

        # Anfangszustand der Schaltflächen
        self.ui.buttonStart.setEnabled(True)
        self.ui.buttonStop.setEnabled(False)
        self.ui.buttonSave.setEnabled(False)

        # Check auto-save setting
        self.ui.autoSave.setChecked(self.save_manager.auto_save)
        self.ui.autoSave.toggled.connect(self._change_auto_save)

    def _setup_radioactive_sample_input(self):
        """
        Initialisiert das Eingabefeld für radioaktive Proben.
        """
        samples = CONFIG["radioactive_samples"]
        radCombo = self.ui.radSample
        radCombo.clear()
        radCombo.addItems(samples)
        Debug.debug(
            f"Radioaktive Proben geladen: {len(samples)} Proben",
        )
        radCombo.setCurrentIndex(-1)  # Kein Standardwert

        # QCompleter für radioaktive Proben
        completer = QCompleter(samples)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        radCombo.setCompleter(completer)

    def _setup_timers(self):
        """
        Richtet alle Timer für die Anwendung ein.

        Messdaten werden im Hintergrund vom ``DeviceManager`` erfasst. Die
        Geräteeinstellungen werden hingegen ausschließlich über diesen Timer
        abgefragt, sobald keine Messung aktiv ist. Dadurch entfällt das
        ``time.sleep`` in der Erfassungsschleife und die UI bleibt reaktionsfähig.
        """
        # Timer für Steuerelemente-Updates
        self.control_update_timer = QTimer(self)
        self.control_update_timer.timeout.connect(self._update_control_display)
        self.control_update_timer.start(CONFIG["timers"]["control_update_interval"])

        # Timer für Statistik-Updates (nur noch für UI-Aktualisierung)
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._update_statistics)
        self.stats_timer.start(CONFIG["timers"]["statistics_update_interval"])

    #
    # 2a. MEASUREMENT CONTROL
    #

    def _set_ui_measuring_state(self) -> None:
        """
        Setzt die UI in den Messmodus (Buttons und Timer entsprechend konfigurieren).
        """
        self.control_update_timer.stop()
        self.ui.buttonStart.setEnabled(False)
        self.ui.buttonSetting.setEnabled(False)
        self.ui.buttonStop.setEnabled(True)
        self.ui.buttonSave.setEnabled(False)
        Debug.debug("UI in Messmodus gesetzt")

    def _set_ui_idle_state(self) -> None:
        """
        Setzt die UI in den Ruhemodus (nach beendeter Messung).
        """
        self.control_update_timer.start(CONFIG["timers"]["control_update_interval"])
        self.ui.buttonStart.setEnabled(True)
        self.ui.buttonSetting.setEnabled(True)
        self.ui.buttonStop.setEnabled(False)
        # buttonSave wird separat basierend auf vorhandenen Daten aktiviert
        save_enabled = self.save_manager.has_unsaved()
        self.ui.buttonSave.setEnabled(save_enabled)
        Debug.debug(
            f"UI in Ruhemodus gesetzt (Save-Button: {'aktiviert' if save_enabled else 'deaktiviert'})"
        )

    def _setup_progress_bar(self, duration_seconds: int) -> None:
        """
        Konfiguriert die ProgressBar basierend auf der Messdauer.

        Args:
            duration_seconds (int): Dauer in Sekunden. 999 bedeutet unendliche Dauer.
        """
        if duration_seconds != 999:
            # Endliche Messdauer - Progress Bar mit Timer
            self.ui.progressBar.setMaximum(duration_seconds)
            self.ui.progressBar.setValue(0)
            self._measurement_timer = QTimer(self)
            self._measurement_timer.timeout.connect(self._update_progress)
            self._measurement_timer.start(1000)  # Update every second
            Debug.debug(f"ProgressBar konfiguriert für {duration_seconds} Sekunden")
        else:
            # Unendliche Messdauer - Indeterminate Progress Bar
            self.ui.progressBar.setMaximum(0)
            self.ui.progressBar.setValue(0)
            self._measurement_timer = None
            Debug.debug("ProgressBar konfiguriert für unendliche Messdauer")

    def _stop_progress_bar(self) -> None:
        """
        Stoppt die ProgressBar und den zugehörigen Timer.
        """
        if self._measurement_timer:
            self._measurement_timer.stop()
            self._measurement_timer = None

        # Reset ProgressBar to idle state
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
    # 2. DATENVERARBEITUNG UND STATISTIK
    #

    def handle_data(self, index, value):
        """
        Verarbeitet eingehende Daten vom Gerät.
        Aktualisiert Anzeige, Historie und Plot mit dem Daten-Controller.

        Args:
            index (int): Der Datenpunktindex
            value (float): Der gemessene Wert
        """
        self.data_controller.add_data_point(index, value)
        # Histogram aktualisieren
        values = [p[1] for p in self.data_controller.data_points]
        self.histogram.update_histogram(values)
        # Daten als ungespeichert markieren
        self.data_saved = False
        self.save_manager.mark_unsaved()

        # Save-Button aktivieren wenn wir gerade nicht messen (im Idle-Zustand)
        if not self.is_measuring:
            self.ui.buttonSave.setEnabled(True)

        # Statistiken nur bei jeder 5. Aktualisierung aktualisieren, um die Performance zu verbessern
        # if hasattr(self, "_stats_counter"):
        #     self._stats_counter += 1
        #     if self._stats_counter >= 5:
        #         self._update_statistics()
        #         self._stats_counter = 0
        # else:
        #     self._stats_counter = 0

    def _update_statistics(self):
        """
        Aktualisiert die Statistiken in der Benutzeroberfläche basierend
        auf den aktuellen Daten im DataController.
        """
        try:
            # Statistiken vom DataController holen
            stats = self.data_controller.get_statistics()

            # Nur aktualisieren, wenn Datenpunkte vorhanden sind
            if stats["count"] > 0:
                stats_text = (
                    f"Datenpunkte: {int(stats['count'])} | "
                    f"Min: {stats['min']:.0f} µs | "
                    f"Max: {stats['max']:.0f} µs | "
                    f"Mittelwert: {stats['avg']:.0f} µs"
                )

                # Standardabweichung hinzufügen, wenn genügend Datenpunkte vorhanden
                if stats["count"] > 1:
                    stats_text += f" | σ: {stats['stdev']:.0f} µs"

                # Statusleiste kurzzeitig aktualisieren, wenn eine Messung läuft
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
    # 3. Gerätesteuerung
    #

    def _update_control_display(self):
        """
        Aktualisiert die UI-Anzeige mit den aktuellen Einstellungen vom GM-Zähler.
        """
        try:
            # Frische Daten vom GM-Counter anfordern
            data = self.control.get_settings()
            if not data:
                Debug.error("Keine Daten vom GM-Counter erhalten.")
                return

            # UI-Elemente aktualisieren
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
        """
        Callback für die Änderung der Auto-Save-Einstellung.

        Args:
            checked (bool): Ob Auto-Save aktiviert ist
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

        # Stoppe die Datenerfassung im DeviceManager
        if hasattr(self, "device_manager"):
            try:
                Debug.info("Stoppe Datenerfassung...")
                self.device_manager.stop_acquisition()

                # Wenn ein echtes Gerät verbunden ist, schließe die Verbindung
                if (
                    hasattr(self.device_manager, "device")
                    and self.device_manager.device
                ):
                    Debug.info("Schließe Geräteverbindung...")
                    self.device_manager.device.close()
            except Exception as e:
                Debug.error(f"Fehler beim Herunterfahren des DeviceManagers: {e}")

        # Stoppe alle Timer
        for timer_attr in ["control_update_timer", "stats_timer"]:
            if hasattr(self, timer_attr):
                timer = getattr(self, timer_attr)
                if timer.isActive():
                    Debug.debug(f"Stoppe Timer: {timer_attr}")
                    timer.stop()

        # Event weitergeben
        Debug.info("Anwendung wird geschlossen")
        event.accept()
