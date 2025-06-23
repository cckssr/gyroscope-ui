import json
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QMainWindow,
    QVBoxLayout,
)
from PySide6.QtCore import QTimer  # pylint: disable=no-name-in-module
from src.device_manager import DeviceManager
from src.control import ControlWidget
from src.plot import PlotWidget
from src.debug_utils import Debug
from src.helper_classes import import_config, Statusbar
from src.data_controller import DataController
from pyqt.ui_mainwindow import Ui_MainWindow


# Import settings and messages
CONFIG = import_config()


class MainWindow(QMainWindow):
    """
    Hauptfenster der HRNGGUI-Anwendung.

    Verwaltet die Benutzeroberfläche, die Verbindung zum Gerät und
    die Datenverarbeitung. Die Klasse ist in funktionale Bereiche gegliedert:

    1. Initialisierung und Setup
    2. Datenverarbeitung und Statistik
    3. Messverwaltung
    4. UI-Event-Handler
    5. Gerätesteuerung
    6. Hilfsfunktionen
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
            width=self.ui.timePlot.width(),
            height=self.ui.timePlot.height(),
            dpi=self.logicalDpiX(),
            fontsize=self.ui.timePlot.fontInfo().pixelSize(),
            xlabel=CONFIG["plot"]["x_label"],
            ylabel=CONFIG["plot"]["y_label"],
        )
        QVBoxLayout(self.ui.timePlot).addWidget(self.plot)

    def _setup_data_controller(self):
        """
        Richtet den Daten-Controller ein.
        """
        self.data_controller = DataController(
            plot_widget=self.plot,
            display_widget=self.ui.currentCount,
            max_history=CONFIG["data_controller"]["max_history_size"],
        )

    def _setup_buttons(self):
        """
        Verbindet die Schaltflächen mit ihren jeweiligen Funktionen.
        """
        # Mess-Steuerungsschaltflächen verbinden
        self.ui.buttonStart.clicked.connect(self._start_measurement)
        self.ui.buttonStop.clicked.connect(self._stop_measurement)
        # self.ui.buttonSave.clicked.connect(self._save_measurement)
        self.ui.buttonSetting.clicked.connect(self._apply_settings)

        # Anfangszustand der Schaltflächen
        self.ui.buttonStart.setEnabled(True)
        self.ui.buttonStop.setEnabled(False)
        self.ui.buttonSave.setEnabled(False)

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
        # vllt nicht notwendig (QT automatisch completer)
        # completer = QCompleter(samples)
        # completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        # radCombo.setCompleter(completer)

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

    def _start_measurement(self):
        """Start measurement and adjust UI."""
        if self.device_manager.start_measurement():
            self.is_measuring = True
            self.control_update_timer.stop()
            self.ui.buttonStart.setEnabled(False)
            self.ui.buttonStop.setEnabled(True)
            self.statusbar.temp_message(
                CONFIG["messages"]["measurement_running"],
                CONFIG["colors"]["orange"],
            )

    def _stop_measurement(self):
        """Stop measurement and resume config polling."""
        self.device_manager.stop_measurement()
        self.is_measuring = False
        self.control_update_timer.start(CONFIG["timers"]["control_update_interval"])
        self.ui.buttonStart.setEnabled(True)
        self.ui.buttonStop.setEnabled(False)
        self.statusbar.temp_message(
            CONFIG["messages"]["measurement_stopped"],
            CONFIG["colors"]["red"],
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
        # Daten als ungespeichert markieren
        self.data_saved = False

        # Statistiken nur bei jeder 5. Aktualisierung aktualisieren, um die Performance zu verbessern
        if hasattr(self, "_stats_counter"):
            self._stats_counter += 1
            if self._stats_counter >= 5:
                self._update_statistics()
                self._stats_counter = 0
        else:
            self._stats_counter = 0

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
                    f"Min: {stats['min']:.2f} µs | "
                    f"Max: {stats['max']:.2f} µs | "
                    f"Mittelwert: {stats['avg']:.2f} µs"
                )

                # Standardabweichung hinzufügen, wenn genügend Datenpunkte vorhanden
                if stats["count"] > 1:
                    stats_text += f" | σ: {stats['stdev']:.2f} µs"

                # Status-Text aktualisieren, falls verfügbar
                if hasattr(self.ui, "statusText"):
                    self.ui.statusText.setText(stats_text)

                # Statusleiste kurzzeitig aktualisieren, wenn eine Messung läuft
                if self.is_measuring:
                    self.statusbar.temp_message(
                        stats_text, CONFIG["colors"]["blue"], duration=1500
                    )

        except Exception as e:
            Debug.error(
                f"Fehler beim Aktualisieren der Statistiken: {e}", exc_info=True
            )

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

    def closeEvent(self, event):
        """
        Wird aufgerufen, wenn das Fenster geschlossen wird.
        Sorgt für ein sauberes Herunterfahren aller Komponenten.

        Args:
            event: Das Close-Event
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
