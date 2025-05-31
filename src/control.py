import time
from PySide6.QtWidgets import QWidget  # pylint: disable=no-name-in-module
from PySide6.QtCore import QTimer  # pylint: disable=no-name-in-module
from pyqt.ui_control import Ui_Form
from src.arduino import GMCounter
from src.debug_utils import Debug


class ControlWindow(QWidget):
    def __init__(self, device_manager=None, parent=None):
        """
        Initializes the control window.

        Args:
            device_manager: The device manager for controlling the GM counter
            parent: Parent widget
        """
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Store device manager reference
        self.device_manager = device_manager
        self.gm_counter = None

        # Initialize GM counter if device manager is available
        if self.device_manager and hasattr(self.device_manager, "arduino"):
            if self.device_manager.port != "/dev/ttymock":
                try:
                    # If device_manager.arduino is already a GMCounter, use that
                    if isinstance(self.device_manager.arduino, GMCounter):
                        self.gm_counter = self.device_manager.arduino
                    else:
                        # Otherwise create a new GMCounter with the same port
                        self.gm_counter = GMCounter(self.device_manager.port)
                except Exception as e:
                    Debug.error(
                        f"Fehler beim Initialisieren des GM-Zählers: {e}", exc_info=e
                    )

        # Connect UI controls to actions
        self.ui.controlButton.clicked.connect(self._apply_settings)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(1000)  # Update every second

        # Initial UI update
        self._update_display()

    def _apply_settings(self):
        """
        Apply all settings to the GM counter.
        """
        if not self.gm_counter:
            return

        try:
            # Get values from UI
            repeat = self.ui.sModeMulti.isChecked()
            auto_query = self.ui.sQModeAuto.isChecked()
            duration_index = self.ui.sDuration.currentIndex()
            voltage = self.ui.sVoltage.value()

            # Apply to GM counter
            self.gm_counter.set_repeat(repeat)
            self.gm_counter.set_stream(4 if auto_query else 1)
            self.gm_counter.set_counting_time(duration_index)
            self.gm_counter.set_voltage(voltage)

            time.sleep(0.2)  # Wait for settings to apply

            # Update UI to reflect the changes
            self._update_display()

            # Show confirmation message
            Debug.info("Einstellungen erfolgreich angewendet.")

        except Exception as e:
            Debug.error(f"Fehler beim Anwenden der Einstellungen: {e}", exc_info=e)

    def _update_display(self):
        """
        Update the UI display with current settings from the GM counter.
        """
        if not self.gm_counter:
            return

        try:
            # Frische Daten vom GM-Counter anfordern
            # Get current data if available
            data = self.gm_counter.get_data()

            # Update device information (nicht zu oft, um Netzwerkverkehr zu reduzieren)
            if not hasattr(self, "_info_updated") or self._info_updated <= 0:
                info = self.gm_counter.get_information()
                self.ui.cVersion.setText(info.get("version", "unbekannt"))
                self._info_updated = 10  # Info nur jede 10. Aktualisierung holen
            else:
                self._info_updated -= 1

            # Update voltage display and spinner
            voltage = data.get("voltage", 500)
            self.ui.cVoltage.display(voltage)

            # Count time based on index values
            counting_time = data.get("counting_time", 0)
            count_time_map = {0: 999, 1: 1, 2: 10, 3: 60, 4: 100, 5: 300}
            count_time = count_time_map.get(counting_time, 999)
            self.ui.cDuration.display(count_time)

            # Update query mode based on stream setting
            stream_mode = data.get("stream", 0)
            stream_mode_map = {
                0: "Keine Abfrage",
                1: "Wenn fertig",
                2: "Einmalig",
                3: "Einmalig und Fertig",
                4: "Automatisch",
            }
            auto_query = stream_mode_map.get(stream_mode, "Unbekannt")
            self.ui.cQueryMode.setText(auto_query)

            # Update mode displays and radio buttons
            is_repeat = data.get("repeat", False)
            self.ui.cMode.setText("Wiederholung" if is_repeat else "Einzel")

            # Update measurement values (use direct member references for dynamically created displays)
            # if hasattr(self, "cCurrentCount"):
            #     last_count = data.get("last_count", 0)
            #     self.cCurrentCount.display(last_count)

            # if hasattr(self, "cProgress"):
            #     progress = data.get("progress", 0)
            #     self.cProgress.display(progress)

        except Exception as e:
            Debug.error(f"Fehler beim Aktualisieren der Anzeige: {e}", exc_info=e)

    def enable_controls(self, enabled=True):
        """
        Enable or disable the control button based on measurement state.

        Args:
            enabled (bool): True to enable controls, False to disable
        """
        self.ui.controlButton.setEnabled(enabled)

    def closeEvent(self, event):
        """
        Stop the timer when the window is closed.
        """
        if hasattr(self, "update_timer"):
            self.update_timer.stop()
        event.accept()
