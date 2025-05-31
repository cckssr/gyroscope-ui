#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Hauptfenster der HRNGGUI-Anwendung.
"""

import csv
import time
from typing import Optional, Dict, Any, List, Tuple

from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QMainWindow,
    QVBoxLayout,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import QTimer, Qt  # pylint: disable=no-name-in-module

from pyqt.ui_mainwindow import Ui_MainWindow
from src.helper_classes import Statusbar, AlertWindow
from src.connection import DeviceManager
from src.plot import PlotWidget
from src.debug_utils import Debug
from src.arduino import GMCounter
from src.data_controller import DataController
from src.config import (
    MAX_PLOT_POINTS,
    PLOT_X_LABEL,
    PLOT_Y_LABEL,
    CONTROL_UPDATE_INTERVAL,
    STATISTICS_UPDATE_INTERVAL,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_ORANGE,
    COLOR_BLUE,
    MSG_APP_INIT,
    MSG_CONNECTED,
    MSG_MEASUREMENT_RUNNING,
    MSG_MEASUREMENT_STOPPED,
    MSG_MEASUREMENT_ENDED,
    MSG_SETTINGS_APPLIED,
    MSG_DATA_SAVED,
    MSG_NO_DATA,
    MSG_UNSAVED_DATA,
)


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
        self.statusbar.temp_message(MSG_APP_INIT)

        # Geräte-Manager einrichten
        self._setup_device_manager(device_manager)

        # UI-Komponenten initialisieren
        self._setup_plot()
        self._setup_data_controller()
        self._setup_buttons()
        self._setup_controls()
        self._setup_timers()

        # Erste Aktualisierung der UI
        self._update_control_display()

        # Erfolgsmeldung anzeigen
        self.statusbar.temp_message(
            MSG_CONNECTED.format(self.device_manager.port),
            COLOR_GREEN,
        )

    #
    # 1. INITIALISIERUNG UND SETUP
    #

    def _setup_device_manager(self, device_manager: DeviceManager):
        """
        Richtet den Geräte-Manager und die GM-Zähler-Verbindung ein.

        Args:
            device_manager (DeviceManager): Der zu verwendende Geräte-Manager
        """
        self.device_manager = device_manager
        self.device_manager.data_callback = self.handle_data
        self.device_manager.status_callback = self.statusbar.temp_message

        # GM-Zähler initialisieren, falls Geräte-Manager verfügbar
        self.gm_counter = None
        if self.device_manager and hasattr(self.device_manager, "arduino"):
            if self.device_manager.port != "/dev/ttymock":
                try:
                    # Wenn device_manager.arduino bereits ein GMCounter ist, diesen verwenden
                    if isinstance(self.device_manager.arduino, GMCounter):
                        self.gm_counter = self.device_manager.arduino
                    else:
                        # Ansonsten neuen GMCounter mit dem gleichen Port erstellen
                        self.gm_counter = GMCounter(self.device_manager.port)
                except Exception as e:
                    Debug.error(
                        f"Fehler beim Initialisieren des GM-Zählers: {e}", exc_info=e
                    )

    def _setup_plot(self):
        """
        Richtet das Plot-Widget ein.
        """
        self.plot = PlotWidget(
            max_plot_points=MAX_PLOT_POINTS,
            width=self.ui.timePlot.width(),
            height=self.ui.timePlot.height(),
            dpi=self.logicalDpiX(),
            fontsize=self.ui.timePlot.fontInfo().pixelSize(),
            xlabel=PLOT_X_LABEL,
            ylabel=PLOT_Y_LABEL,
        )
        QVBoxLayout(self.ui.timePlot).addWidget(self.plot)

    def _setup_data_controller(self):
        """
        Richtet den Daten-Controller ein.
        """
        self.data_controller = DataController(
            plot_widget=self.plot,
            display_widget=self.ui.currentCount,
            # history_widget ist optional und wird hier nicht verwendet
        )

    def _setup_buttons(self):
        """
        Verbindet die Schaltflächen mit ihren jeweiligen Funktionen.
        """
        # Mess-Steuerungsschaltflächen verbinden
        self.ui.buttonStart.clicked.connect(self._start_measurement)
        self.ui.buttonStop.clicked.connect(lambda: self._update_measurement(False))

        # Speicherschaltfläche verbinden, falls vorhanden
        if hasattr(self.ui, "buttonSave"):
            self.ui.buttonSave.clicked.connect(self._save_measurement)
            # Speicherschaltfläche zunächst deaktivieren
            self.ui.buttonSave.setEnabled(False)

        # Anfangszustand der Schaltflächen
        self.ui.buttonStart.setEnabled(True)
        self.ui.buttonStop.setEnabled(False)

    def _setup_controls(self):
        """
        Verbindet die Steuerelemente mit ihren jeweiligen Funktionen.
        """
        # Modus-Radiobuttons verbinden, falls vorhanden
        if hasattr(self.ui, "sModeSingle") and hasattr(self.ui, "sModeMulti"):
            self.ui.sModeSingle.toggled.connect(self._on_mode_changed)
            self.ui.sModeMulti.toggled.connect(self._on_mode_changed)

        # Abfragemodus-Radiobuttons verbinden, falls vorhanden
        if hasattr(self.ui, "sQModeMan") and hasattr(self.ui, "sQModeAuto"):
            self.ui.sQModeMan.toggled.connect(self._on_query_mode_changed)
            self.ui.sQModeAuto.toggled.connect(self._on_query_mode_changed)

        # Dauer-Dropdown verbinden, falls vorhanden
        if hasattr(self.ui, "sDuration"):
            self.ui.sDuration.currentIndexChanged.connect(self._on_duration_changed)

        # Spannungs-Spinner und Dial verbinden, falls vorhanden
        if hasattr(self.ui, "sVoltage") and hasattr(self.ui, "voltDial"):
            self.ui.sVoltage.valueChanged.connect(self._on_voltage_changed)
            self.ui.voltDial.valueChanged.connect(self.ui.sVoltage.setValue)
            self.ui.sVoltage.valueChanged.connect(self.ui.voltDial.setValue)

        # Steuerungsschaltfläche verbinden
        if hasattr(self.ui, "setControl"):
            self.ui.setControl.clicked.connect(self._apply_settings)

    def _setup_timers(self):
        """
        Richtet alle Timer für die Anwendung ein.
        """
        # Haupt-Timer einrichten
        self.timer = QTimer()
        self.timer.setInterval(100)

        # Timer für Steuerelemente-Updates
        self.control_update_timer = QTimer(self)
        self.control_update_timer.timeout.connect(self._update_control_display)
        self.control_update_timer.start(CONTROL_UPDATE_INTERVAL)

        # Timer für Statistik-Updates
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._update_statistics)
        self.stats_timer.start(STATISTICS_UPDATE_INTERVAL)

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
                    self.statusbar.temp_message(stats_text, COLOR_BLUE, duration=1500)

        except Exception as e:
            Debug.error(
                f"Fehler beim Aktualisieren der Statistiken: {e}", exc_info=True
            )

    #
    # 3. MESSVERWALTUNG
    #

    def _start_measurement(self):
        """
        Überprüft, ob die aktuellen Daten gespeichert sind, bevor eine neue Messung gestartet wird.
        """
        if not self.data_saved and len(self.data_controller.data_points) > 0:
            # Benutzer fragen, ob ungespeicherte Daten überschrieben werden sollen
            reply = QMessageBox.question(
                self,
                "Ungespeicherte Daten",
                MSG_UNSAVED_DATA,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Alte Daten löschen
                self.data_controller.clear_data()
                self._update_measurement(True)
            # Keine Aktion, wenn der Benutzer nicht überschreiben möchte
        else:
            # Keine ungespeicherten Daten, Messung direkt starten
            self.data_controller.clear_data()
            self._update_measurement(True)

    def _update_measurement(self, checked: bool):
        """
        Aktualisiert den Messstatus basierend auf dem gegebenen Wert.

        Args:
            checked (bool): True zum Starten, False zum Stoppen der Messung
        """
        self.is_measuring = checked
        if checked:
            self.ui.buttonStart.setEnabled(False)
            self.ui.buttonStop.setEnabled(True)
            # Status während der Messung auf Orange ändern
            self.statusbar.temp_message(MSG_MEASUREMENT_RUNNING, COLOR_ORANGE)
            self.device_manager.start_acquisition()

            # Kontrollelemente während der Messung deaktivieren
            self.enable_controls(False)

            # Messung am GM-Zähler starten, falls verfügbar
            if self.gm_counter:
                self.gm_counter.set_counting(True)
        else:
            self.ui.buttonStart.setEnabled(True)
            self.ui.buttonStop.setEnabled(False)
            self.device_manager.stop_acquisition()
            self.statusbar.temp_message(MSG_MEASUREMENT_STOPPED, COLOR_RED, 1500)

            # Statistiken anzeigen, wenn verfügbar
            if len(self.data_controller.data_points) > 0:
                self._update_statistics()

            self.statusbar.temp_message(MSG_MEASUREMENT_ENDED, COLOR_GREEN)

            # Kontrollelemente nach der Messung aktivieren
            self.enable_controls(True)

            # Messung am GM-Zähler stoppen, falls verfügbar
            if self.gm_counter:
                self.gm_counter.set_counting(False)

            # Speicherschaltfläche aktivieren, wenn Daten zum Speichern vorhanden sind
            if (
                hasattr(self.ui, "buttonSave")
                and len(self.data_controller.data_points) > 0
            ):
                self.ui.buttonSave.setEnabled(True)

    def _save_measurement(self):
        """
        Speichert die aktuellen Messdaten in eine CSV-Datei.
        """
        if not self._has_data_to_save():
            return

        file_path = self._get_save_file_path()
        if not file_path:
            return

        try:
            self._write_data_to_csv(file_path)
            self._handle_successful_save(file_path)
        except Exception as e:
            self._handle_save_error(e)

    def _has_data_to_save(self) -> bool:
        """Überprüft, ob Daten zum Speichern vorhanden sind."""
        if len(self.data_controller.data_points) == 0:
            QMessageBox.information(
                self,
                "Keine Daten",
                MSG_NO_DATA,
                QMessageBox.StandardButton.Ok,
            )
            return False
        return True

    def _get_save_file_path(self) -> str:
        """Öffnet den Dateidialog und gibt den gewählten Dateipfad zurück."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Messdaten speichern", "", "CSV-Dateien (*.csv);;Alle Dateien (*)"
        )
        return file_path

    def _write_data_to_csv(self, file_path: str):
        """Schreibt die Messdaten in eine CSV-Datei."""
        with open(file_path, "w", newline="", encoding="UTF-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Index", "Wert (µs)"])
            for idx, value in self.data_controller.data_points:
                writer.writerow([idx, value])

    def _handle_successful_save(self, file_path: str):
        """Behandelt den erfolgreichen Speichervorgang."""
        self.data_saved = True
        self.statusbar.temp_message(MSG_DATA_SAVED.format(file_path), COLOR_GREEN)
        # Speicherschaltfläche nach erfolgreichem Speichern deaktivieren
        if hasattr(self.ui, "buttonSave"):
            self.ui.buttonSave.setEnabled(False)

    def _handle_save_error(self, error: Exception):
        """Behandelt Fehler beim Speichern der Daten."""
        QMessageBox.critical(
            self,
            "Speicherfehler",
            f"Fehler beim Speichern der Daten: {str(error)}",
            QMessageBox.StandardButton.Ok,
        )
        Debug.error(f"Fehler beim Speichern der Messdaten: {error}")

    #
    # 4. UI-EVENT-HANDLER
    #

    def _on_mode_changed(self, checked):
        """
        Behandelt Änderungen an den Modus-Radiobuttons.
        """
        if not checked:
            return

        repeat = self.ui.sModeMulti.isChecked()
        self.ui.cMode.setText("Wiederholung" if repeat else "Einzel")

    def _on_query_mode_changed(self, checked):
        """
        Behandelt Änderungen an den Abfragemodus-Radiobuttons.
        """
        if not checked:
            return

        auto = self.ui.sQModeAuto.isChecked()
        self.ui.cQueryMode.setText("Automatisch" if auto else "Manuell")

    def _on_duration_changed(self, index):
        """
        Behandelt Änderungen am Dauer-Dropdown.
        """
        # LCD-Anzeige auf den ausgewählten Wert setzen
        duration_values = [999, 1, 10, 60, 100, 300]  # 999 für unendlich
        if index >= 0 and index < len(duration_values):
            self.ui.cDuration.display(duration_values[index])

    def _on_voltage_changed(self, value):
        """
        Behandelt Änderungen am Spannungs-Spinner.
        """
        self.ui.cVoltage.display(value)

    def _open_alert(self):
        """
        Öffnet das Warnfenster.
        """
        alert = AlertWindow(self)
        alert.exec()

    #
    # 5. GERÄTESTEUERUNG
    #

    def _apply_settings(self):
        """
        Wendet alle Einstellungen auf den GM-Zähler an.
        """
        if not self.gm_counter:
            return

        try:
            # Werte aus der UI abrufen
            repeat = self.ui.sModeMulti.isChecked()
            auto_query = self.ui.sQModeAuto.isChecked()
            duration_index = self.ui.sDuration.currentIndex()
            voltage = self.ui.sVoltage.value()

            # Auf GM-Zähler anwenden
            self.gm_counter.set_repeat(repeat)
            self.gm_counter.set_stream(3 if auto_query else 0)
            self.gm_counter.set_counting_time(duration_index)
            self.gm_counter.set_voltage(voltage)

            # Frische Daten anfordern, um die Änderungen widerzuspiegeln
            self.gm_counter.send_command("b2")  # Jetzt vollständige Daten anfordern

            # Kurze Wartezeit, um sicherzustellen, dass die Änderungen angewendet werden
            time.sleep(0.2)

            # UI aktualisieren, um die Änderungen widerzuspiegeln
            self._update_control_display()

            # Bestätigungsmeldung anzeigen
            self.statusbar.temp_message(MSG_SETTINGS_APPLIED, COLOR_GREEN)

        except Exception as e:
            Debug.error(f"Fehler beim Anwenden der Einstellungen: {e}", exc_info=e)
            self.statusbar.temp_message(f"Fehler: {e}", COLOR_RED)

    def _update_control_display(self):
        """
        Aktualisiert die UI-Anzeige mit den aktuellen Einstellungen vom GM-Zähler.
        """
        if not self.gm_counter:
            return

        try:
            # Frische Daten vom GM-Counter anfordern
            data = self.gm_counter.get_data()

            self._update_device_info()
            self._update_voltage_display(data)
            self._update_mode_display(data)
            self._update_query_mode_display(data)
            self._update_counting_time_display(data)

        except Exception as e:
            Debug.error(f"Fehler bei der Aktualisierung der Anzeige: {e}")

    def _update_device_info(self):
        """Aktualisiert die Geräteinformationen (nicht zu oft, um Netzwerkverkehr zu reduzieren)."""
        if not self.gm_counter:
            return

        if not hasattr(self, "_info_updated") or self._info_updated <= 0:
            try:
                info = self.gm_counter.get_information()
                self.ui.cVersion.setText(info.get("version", "unbekannt"))
                self._info_updated = 10  # Info nur jede 10. Aktualisierung holen
            except Exception:
                self.ui.cVersion.setText("Fehler")
                self._info_updated = 20  # Bei Fehler längere Pause
        else:
            self._info_updated -= 1

    def _update_voltage_display(self, data):
        """Aktualisiert die Spannungsanzeige und den Spinner."""
        voltage = data.get("voltage", 500)
        self.ui.cVoltage.display(voltage)
        # Spinner aktualisieren, ohne _on_voltage_changed auszulösen
        self.ui.sVoltage.blockSignals(True)
        self.ui.sVoltage.setValue(voltage)
        self.ui.sVoltage.blockSignals(False)

    def _update_mode_display(self, data):
        """Aktualisiert die Modusanzeige und die Radiobuttons."""
        is_repeat = bool(data.get("repeat", False))
        self.ui.cMode.setText("Wiederholung" if is_repeat else "Einzel")
        # Radiobuttons aktualisieren, ohne Signale auszulösen
        self.ui.sModeSingle.blockSignals(True)
        self.ui.sModeMulti.blockSignals(True)
        self.ui.sModeMulti.setChecked(is_repeat)
        self.ui.sModeSingle.setChecked(not is_repeat)
        self.ui.sModeSingle.blockSignals(False)
        self.ui.sModeMulti.blockSignals(False)

    def _update_query_mode_display(self, data):
        """Aktualisiert den Abfragemodus basierend auf der Stream-Einstellung."""
        stream_mode = data.get("stream", 0)
        auto_query = stream_mode > 0
        self.ui.cQueryMode.setText("Automatisch" if auto_query else "Manuell")
        # Radiobuttons aktualisieren, ohne Signale auszulösen
        self.ui.sQModeMan.blockSignals(True)
        self.ui.sQModeAuto.blockSignals(True)
        self.ui.sQModeAuto.setChecked(auto_query)
        self.ui.sQModeMan.setChecked(not auto_query)
        self.ui.sQModeMan.blockSignals(False)
        self.ui.sQModeAuto.blockSignals(False)

    def _update_counting_time_display(self, data):
        """Aktualisiert die Anzeige der Zählzeitbasis."""
        counting_time = data.get("counting_time", 0)
        from src.config import COUNT_TIME_MAP

        count_time = COUNT_TIME_MAP.get(counting_time, 999)
        self.ui.cDuration.display(count_time)

        # Dropdown aktualisieren, ohne Signal auszulösen
        self.ui.sDuration.blockSignals(True)
        self.ui.sDuration.setCurrentIndex(counting_time)
        self.ui.sDuration.blockSignals(False)

    #
    # 6. HILFSFUNKTIONEN
    #

    def enable_controls(self, enabled=True):
        """
        Aktiviert oder deaktiviert die Steuerungsschaltfläche basierend auf dem Messzustand.

        Args:
            enabled (bool): True zum Aktivieren, False zum Deaktivieren
        """
        if hasattr(self.ui, "setControl"):
            self.ui.setControl.setEnabled(enabled)

    def closeEvent(self, event):
        """
        Behandelt das Schließen-Ereignis des Fensters.
        Stellt sicher, dass alle Threads vor dem Schließen gestoppt werden.
        """
        # Laufende Messungen/Threads stoppen
        if self.is_measuring:
            self.device_manager.stop_acquisition()

        # Timer stoppen, falls sie laufen
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()

        if (
            hasattr(self, "control_update_timer")
            and self.control_update_timer.isActive()
        ):
            self.control_update_timer.stop()

        if hasattr(self, "stats_timer") and self.stats_timer.isActive():
            self.stats_timer.stop()

        # Sicherstellen, dass die Anwendung vollständig beendet wird
        from PySide6.QtWidgets import QApplication

        QApplication.quit()

        # Schließen-Ereignis akzeptieren
        event.accept()
