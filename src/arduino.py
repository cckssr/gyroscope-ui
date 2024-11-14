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

class Arduino:
    """
    A class to represent an Arduino connection.

    Attributes
    ----------
    port : str
        The port to which the Arduino is connected.
    rate : int, optional
        The baud rate for the serial communication (default is 115200).
    arduino : Serial or None
        The Serial object representing the connection to the Arduino.
    """
    def __init__(self, port, rate=115200):
        self.port = port
        self.rate = rate
        self.arduino = None
        self.reconnect()

    def reconnect(self):
        """
        Reconnects to the Arduino device.
        This method closes the existing connection to the Arduino device if it is open,
        and then establishes a new connection using the specified port and baud rate.
        Raises:
            SerialException: If there is an issue opening the serial port.
        """
        if self.arduino and self.arduino.isOpen():
            self.arduino.close()
        try:
            self.arduino = Serial(port=self.port, baudrate=self.rate)
        except SerialException as e:
            print(f"Error: Could not open port {self.port}. {e}")
            self.arduino = None

    def status(self):
        """
        Check the status of the Arduino connection.
        Returns:
            bool: True if the Arduino connection is open, False otherwise.
        """
        return self.arduino.isOpen() if self.arduino else False

    def close(self):
        """
        Closes the connection to the Arduino if it is open.
        This method checks if the `arduino` attribute is set and, if so, 
        calls its `close` method to terminate the connection.
        """
        if self.arduino:
            self.arduino.close()

    def read(self):
        """
        Reads a line from the Arduino serial connection.
        Returns:
            str: The line read from the Arduino if the connection is established.
            None: If the Arduino connection is not established.
        """
        return self.arduino.readline() if self.arduino else None

    def write(self, value, encoding="UTF-8"):
        """
        Writes a value to the Arduino device.
        Args:
            value (str): The string value to be written to the Arduino.
            encoding (str, optional): The encoding to use for the string. Defaults to "UTF-8".
        Returns:
            None
        """
        if self.arduino:
            self.arduino.write(value.encode(encoding))
