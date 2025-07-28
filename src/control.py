import time
from typing import Union
from src.debug_utils import Debug
from src.device_manager import DeviceManager
from src.helper_classes import import_config

CONFIG = import_config()


class ControlWidget:
    def __init__(self, device_manager: DeviceManager):
        """
        Initializes the hardware control widget to display and set GM counter parameters.

        Args:
            device_manager: The device manager for controlling the GM counter
        """
        # Store device manager reference
        self.device_manager = device_manager
        self.gm_counter = device_manager.device
        self.measurement_active = False

        if not self.device_manager:
            Debug.error("Device manager is not available.")
            return

    def apply_settings(self, settings: dict[str, Union[bool, int]]) -> bool:
        """
        Apply all settings to the GM counter.
        """
        try:
            # Get values from UI
            repeat = settings.get("repeat", False)
            auto_query = settings.get("auto_query", False)
            duration_index = int(
                settings.get("counting_time", 0)
            )  # duration as integer
            voltage = settings.get("voltage", 500)

            Debug.debug(
                f"Einstellungen: repeat={repeat}, auto_query={auto_query}, "
                f"duration (index)={duration_index}, voltage={voltage}"
            )

            # Apply to GM counter
            self.gm_counter.set_repeat(repeat)
            self.gm_counter.set_stream(4 if auto_query else 1)
            self.gm_counter.set_counting_time(duration_index)
            self.gm_counter.set_voltage(voltage)

            time.sleep(0.2)  # Wait for settings to apply

            # Show confirmation message
            Debug.debug("Einstellungen erfolgreich angewendet.")

            return True

        except Exception as e:
            Debug.error(f"Fehler beim Anwenden der Einstellungen: {e}", exc_info=e)
            return False

    def get_settings(self) -> dict[str, Union[bool, int]]:
        """
        Retrieve the current settings from the GM counter.

        Returns:
            dict[str, Union[bool, int]]: The current counter settings.
        """
        try:
            data = self.gm_counter.get_data()
            if not data:
                Debug.error("Keine Daten vom GM-Counter erhalten.")
                return {}

            # Check if measurement is active (started from hardware)
            if not self.measurement_active and data["progress"] > 0:
                self.measurement_active = True
                Debug.info("Messung wurde gestartet.")
            return data

        except Exception as e:
            Debug.error(f"Fehler beim Abrufen der Einstellungen: {e}", exc_info=e)
            return {}

    def reset_settings(self) -> bool:
        """
        Reset the GM counter settings to default values.
        """
        try:
            # Reset to default values
            self.gm_counter.set_repeat(False)
            self.gm_counter.set_stream(0)  # No streaming
            self.gm_counter.set_counting_time(0)  # Unlimited
            self.gm_counter.set_voltage(500)  # Default voltage

            time.sleep(0.2)  # Wait for reset to apply

            Debug.debug("Einstellungen erfolgreich zurückgesetzt.")
            return True

        except Exception as e:
            Debug.error(f"Fehler beim Zurücksetzen der Einstellungen: {e}", exc_info=e)
            return False

    def get_device_info(self) -> dict:
        """
        Retrieve device information from the GM counter.
        """
        try:
            info = self.gm_counter.get_information()
            Debug.debug(f"Geräteinformationen abgerufen: {info}")
            return info

        except Exception as e:
            Debug.error(f"Fehler beim Abrufen der Geräteinformationen: {e}", exc_info=e)
            return {}
