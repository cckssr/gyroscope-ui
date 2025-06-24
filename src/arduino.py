#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
arduino.py

This module provides a class to manage a serial connection to an Arduino device.

Classes:
    Arduino: A class to represent an Arduino connection, providing methods to
             reconnect, check status, close the connection, read from, and write to the Arduino.

Usage example:
    arduino = Arduino(port='/dev/ttyUSB0')
    if arduino.connected:
        arduino.send_command('Hello, Arduino!')
        print(arduino.read_value())
"""
from typing import Optional, Union, Dict, Any
from time import sleep
import serial
from src.debug_utils import Debug


class Arduino:
    """
    Class for communication with Arduino-based devices.
    Manages serial connection and data exchange with hardware.
    """

    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0):
        """
        Initialize Arduino connection.

        Args:
            port (str): Serial port identifier
            baudrate (int, optional): Communication speed. Defaults to 9600.
            timeout (float, optional): Read timeout in seconds. Defaults to 1.0.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        self.connected = False
        self._config: Dict[str, Any] = {}

    def reconnect(self) -> bool:
        """
        (Re-)establishes connection with the Arduino.

        Returns:
            bool: True if connection successful, False otherwise

        Raises:
            serial.SerialException: If connection fails
        """
        # Close existing connection if any
        if self.serial and self.serial.is_open:
            self.serial.close()
            Debug.debug(f"Closed existing connection to {self.port}")
            sleep(0.5)  # Give the port time to close properly

        try:
            Debug.info(f"Attempting to connect to {self.port} at {self.baudrate} baud")
            self.serial = serial.Serial(
                port=self.port, baudrate=self.baudrate, timeout=self.timeout
            )
            sleep(2.0)  # Allow Arduino to reset after connection
            self.serial.read_all()  # Clear any existing data in the buffer
            self.serial.flush()  # Clear the serial buffer
            self.connected = True
            Debug.info(f"Successfully connected to {self.port}")
            return True
        except serial.SerialException as e:
            self.connected = False
            Debug.error(f"Failed to connect to {self.port}: {e}")
            raise e

    def close(self) -> None:
        """
        Closes the connection to the Arduino.
        """
        if self.serial and self.serial.is_open:
            self.serial.close()
            Debug.debug(f"Connection to {self.port} closed")
        self.connected = False

    def send_command(self, command: str) -> bool:
        """
        Sends a command to the Arduino.

        Args:
            command (str): Command to send

        Returns:
            bool: True if command sent successfully, False otherwise
        """
        if not self.serial or not self.serial.is_open:
            Debug.error("Cannot send command: Serial connection not open")
            return False

        try:
            # Ensure command ends with a newline
            if not command.endswith("\n"):
                command += "\n"
            self.serial.write(command.encode("utf-8"))
            self.serial.flush()
            Debug.debug(f"Command sent: {command.strip()}")
            return True
        except Exception as e:
            Debug.error(
                f"Error sending command '{command.strip()}': {e}", exc_info=True
            )
            return False

    def read_value(self) -> Union[int, float, str, None]:
        """
        Reads a single value from the Arduino,
        ensuring a complete line is read until a newline or carriage return.

        Returns:
            Union[int, float, str, None]: The value read, or None if reading failed
        """
        if not self.serial or not self.serial.is_open:
            Debug.error("Error: Serial connection not open")
            return None

        try:
            # Wait briefly to ensure data has arrived
            sleep(0.2)

            # Check if there is data available to read
            if self.serial.in_waiting > 0:
                # Read until newline or carriage return
                response = self.serial.readline()
                response = response.decode("utf-8").strip()

                # Debug output
                Debug.debug(f"Received raw data: '{response}'")

                # Check if the response is empty or invalid
                if not response:
                    Debug.info("Empty response received")
                    return None
                if response.lower() == "invalid":
                    Debug.info("'invalid' response received")
                    return None

                # Return the raw response
                return response
            else:
                Debug.info("No data available to read")
                return None
        except (serial.SerialException, UnicodeDecodeError) as e:
            Debug.error(f"Error reading value: {e}", exc_info=True)
            return None

    def set_config(self, key: str, value: Any) -> bool:
        """
        Sets a configuration parameter for the Arduino.

        Args:
            key (str): Configuration parameter name
            value (Any): Configuration parameter value

        Returns:
            bool: True if configuration was set successfully, False otherwise
        """
        self._config[key] = value
        return self.send_command(f"CONFIG {key}={value}")

    def get_config(self, key: str) -> Any:
        """
        Retrieves a configuration parameter.

        Args:
            key (str): Configuration parameter name

        Returns:
            Any: The configuration parameter value
        """
        return self._config.get(key, None)


class GMCounter(Arduino):
    """
    A class to represent a GM counter connected to an Arduino.
    Class only for communication with GM counters and basic validity checks.

    Inherits from the Arduino class and provides additional functionality specific to GM counters.
    """

    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0):
        super().__init__(port, baudrate, timeout)
        self.reconnect()
        sleep(1)  # Allow time for the Arduino to reset
        self.reconnect()  # Ensure the connection is established
        Debug.info("Initializing GMCounter...")
        self.set_stream(0)  # Stop any streaming by default
        self.clear_register()
        sleep(1)  # Allow time for the Arduino to reset
        init_value = self.read_value()
        while init_value != "" and init_value is not None:
            Debug.debug(f"Initial value read: {init_value}")
            self.set_stream(0)  # Stop any streaming by default
            init_value = self.read_value()
            sleep(0.5)

    def get_data(self, request: bool = True) -> Dict[str, Union[int, bool]]:
        """
        Extracts data from the GM counter data string stream.

        Returns:
            dict: A dictionary containing the extracted data.
        """
        data = {
            "count": 0,
            "last_count": 0,
            "counting_time": 0,
            "repeat": False,
            "progress": 0,
            "voltage": 0,
        }

        if request:
            Debug.info("Requesting data from GMCounter...")
            self.send_command("b2")  # Request single data read

        # Read data with logging
        Debug.debug("Attempting to read data from GMCounter...")
        line = self.read_value()

        if line:
            Debug.debug(f"Processing data line: '{line}'")
            try:
                parts = str(line).split(",")
                if parts[-1] == "":  # Remove empty last part if present
                    parts = parts[:-1]
                Debug.debug(f"Split into {len(parts)} parts: {parts}")

                # Only process data if we have the expected number of parts
                if len(parts) == len(data):
                    for i, part in enumerate(parts):
                        key = list(data.keys())[i]
                        try:
                            if key == "repeat":
                                data[key] = bool(int(part))
                            else:
                                data[key] = int(part)
                        except ValueError as e:
                            Debug.error(
                                f"Error converting value '{part}' for key '{key}': {e}"
                            )
                            # Keep default value for this field
                else:
                    Debug.info(
                        f"Warning: Received {len(parts)} values instead of {len(data)} expected values."
                    )
            except ValueError as e:
                Debug.error(f"Error parsing line: '{line}'. {e}")
        else:
            Debug.info("No data received from GMCounter")

        Debug.debug(f"Final data: {data}")
        return data

    def set_stream(self, value: int = 0):
        """
        Sets the stream value for the GM counter.

        Args:
            value (int): The stream value to set.
                '0': Stop streaming.
                '1': Send streaming data when the measurement is ready.
                '2': Send streaming data now.
                '3': Send data now and continue when ready ('2' + '1').
                '4': Send data every 50 ms.
                '5': Use a comma as a separator between values.
                '6': Use a semicolon as a separator between values.
                '7': Use a space as a separator between values.
                '8': Use a tab as a separator between values.
        """
        self.send_command(f"b{value}")
        return True

    def get_information(self) -> Dict[str, str]:
        """
        Gets information from the GM counter.

        Returns:
            dict: A dictionary containing the GM counter information.
        """
        info = {"copyright": "", "version": ""}

        Debug.info("Requesting copyright information...")
        self.send_command("c")
        # Give some time for the response
        sleep(0.5)
        line = self.read_value()
        if line:
            try:
                info["copyright"] = str(line)
                Debug.info(f"Copyright info: {info['copyright']}")
            except ValueError as e:
                Debug.error(f"Error parsing copyright line: {line}. {e}")
                info["copyright"] = "Error"
        else:
            Debug.info("No copyright information received")

        Debug.info("Requesting version information...")

        self.send_command("v")
        # Give some time for the response
        sleep(0.5)
        line = self.read_value()
        if line:
            try:
                info["version"] = str(line)
                Debug.info(f"Version info: {info['version']}")
            except ValueError as e:
                Debug.error(f"Error parsing version line: {line}. {e}", exc_info=True)
                info["version"] = "Error"
        else:
            Debug.info("No version information received")

        return info

    def set_voltage(self, value: int = 500):
        """
        Sets the voltage for the GM counter.

        Args:
            value (int): The voltage value in volt to set (default is 500).
        """
        if not 300 <= value <= 700:
            Debug.error("Error: Voltage must be between 300 and 700.")
            return None
        self.send_command(f"j{value}")
        return True

    def set_repeat(self, value: bool = False):
        """
        Sets the repeat mode for the GM counter.

        Args:
            value (bool): True to enable repeat mode, False to disable it.
        """
        self.send_command(f"o{int(value)}")
        return True

    def set_counting(self, value: bool = False):
        """
        Starts or stops the counting process of the GM counter.

        Args:
            value (bool): True to start counting, False to stop it.
        """
        self.send_command(f"s{int(value)}")
        return True

    def set_speaker(self, gm: bool = False, ready: bool = False):
        """
        Sets the speaker settings for the GM counter.
        The speaker settings are represented by a combination of two binary values:
        - 'U0': GM sound off - Ready sound off
        - 'U1': GM sound on - Ready sound off
        - 'U2': GM sound off - Ready sound on
        - 'U3': GM sound on - Ready sound on

        Args:
            gm (bool): True to enable GM sound, False to disable it.
            ready (bool): True to enable ready sound, False to disable it.
        """
        self.send_command(f"U{int(gm) + 2 * int(ready)}")
        return True

    def set_counting_time(self, value: int = 0):
        """
        Sets the counting time for the GM counter.

        Args:
            value (int): The counting time in seconds (default is 0).

        Possible settings:
            'f0': Infinite
            'f1': 1 second
            'f2': 10 seconds
            'f3': 60 seconds
            'f4': 100 seconds
            'f5': 300 seconds
        """
        if not 0 <= value <= 5:
            Debug.error("Error: Counting time key must be between 0 and 5.")
            return None
        self.send_command(f"f{value}")
        return True

    def clear_register(self):
        """
        Clears the register of the GM counter.
        This is typically used to reset the count.
        """
        self.send_command("w")
        return True
