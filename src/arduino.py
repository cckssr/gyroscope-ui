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
    if arduino.status():
        arduino.write('Hello, Arduino!')
        print(arduino.read())
"""
from serial import Serial, SerialException
from typing import Dict, Union

def check_connection(func):
    """
    Decorator to check the status of the Arduino connection before executing a function.
    
    Returns None if the connection is not active.
    """
    def wrapper(self, *args, **kwargs):
        if not self.status():
            return None
        return func(self, *args, **kwargs)
    return wrapper

class Arduino:
    """
    A class to represent an Arduino connection.

    Attributes:
        port (str): The port to which the Arduino is connected.
        rate (int): The baud rate for the serial communication (default is 115200).
        arduino (Serial or None): The Serial object representing the connection to the Arduino.
    Methods:
        __init__(port: str, rate: int = 115200):
            Initializes the Arduino connection with the specified port and baud rate.
        reconnect():
            Reconnects to the Arduino device.
        status() -> bool:
            Checks the status of the Arduino connection.
        close():
            Closes the connection to the Arduino.
        read() -> str:
            Reads a line from the Arduino serial connection.
        write(value: str, encoding: str = "UTF-8"):
            Writes a value to the Arduino device.
    """
    def __init__(self, port: str, rate: int = 115200):
        self.port = port
        self.rate = rate
        self.arduino = None
        self.reconnect()

    def reconnect(self):
        if self.arduino and self.arduino.isOpen():
            self.arduino.close()
        try:
            self.arduino = Serial(port=self.port, baudrate=self.rate)
        except SerialException as e:
            print(f"Error: Could not open port {self.port}. {e}")
            self.arduino = None

    def status(self) -> bool:
        return self.arduino.isOpen() if self.arduino else False

    def close(self):
        if self.arduino:
            self.arduino.close()

    def read(self) -> str:
        return self.arduino.readline() if self.arduino else None

    def write(self, value: str, encoding: str = "UTF-8"):
        if self.arduino:
            self.arduino.write(value.encode(encoding))

class GMCounter(Arduino):
    """
    A class to represent a GM counter connected to an Arduino.

    Inherits from the Arduino class and provides additional functionality specific to GM counters.
    """
    def __init__(self, port: str, rate: int = 115200):
        super().__init__(port, rate)
        self.reconnect()

    @check_connection
    def get_data(self) -> Dict[str, Union[int, bool]]:
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
            "voltage": 0
        }
        line = self.read()
        if line:
            try:
                parts = line.decode("UTF-8").strip().split(",")
                for i, part in enumerate(parts):
                    key = list(data.keys())[i]
                    if key == "repeat":
                        data[key] = bool(int(part))
                    else:
                        data[key] = int(part)
            except ValueError as e:
                print(f"Error parsing line: {line}. {e}")
        return data

    @check_connection
    def set_stream(self, value: int = 0):
        """
        Sets the stream value for the GM counter.

        Args:
            value (int): The stream value to set.

        Streaming settings:
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
        self.write(f"b{value}")
        return True

    @check_connection
    def get_information(self) -> Dict[str, str]:
        """
        Gets information from the GM counter.

        Returns:
            dict: A dictionary containing the GM counter information.
        """
        info = {
            "copyright": "",
            "version": ""
        }
        self.write("c")
        line = self.read()
        if line:
            try:
                info["copyright"] = line.decode("UTF-8").strip()
            except ValueError as e:
                print(f"Error parsing line: {line}. {e}")
                info["copyright"] = "Error"

        self.write("v")
        line = self.read()
        if line:
            try:
                info["version"] = line.decode("UTF-8").strip()
            except ValueError as e:
                print(f"Error parsing line: {line}. {e}")
                info["version"] = "Error"
        return info

    @check_connection
    def set_voltage(self, value: int = 500):
        """
        Sets the voltage for the GM counter.

        Args:
            value (int): The voltage value in volt to set (default is 500).
        """
        if not 300 <= value <= 700:
            print("Error: Voltage must be between 300 and 700.")
            return None
        self.write(f"j{value}")
        return True

    @check_connection
    def set_repeat(self, value: bool = False):
        """
        Sets the repeat mode for the GM counter.

        Args:
            value (bool): True to enable repeat mode, False to disable it.
        """
        self.write(f"o{int(value)}")
        return True

    @check_connection
    def set_counting(self, value: bool = False):
        """
        Starts or stops the counting process of the GM counter.

        Args:
            value (bool): True to start counting, False to stop it.
        """
        self.write(f"s{int(value)}")
        return True

    @check_connection
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
        self.write(f"U{int(gm) + 2 * int(ready)}")
        return True

    @check_connection
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
            print("Error: Counting time must be between 0 and 5.")
            return None
        self.write(f"f{value}")
        return True
