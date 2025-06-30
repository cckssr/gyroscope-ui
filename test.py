import serial
import os
import time
from tempfile import gettempdir


def check_mock_port():
    """
    Checks if the mock virtual port is available.
    Returns:
        str: The mock port name if available, otherwise None.
    """
    path = os.path.join(gettempdir(), "virtual_serial_port.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            port = f.read().strip()
            return port
    return None


def main():
    """
    Main function to check for the mock port and print its status.
    """
    mock_port = check_mock_port()
    if mock_port:
        print(f"Mock port found: {mock_port}")
    else:
        print("No mock port found. Please run the mock serial device script first.")

    device = serial.Serial(mock_port, baudrate=115200)
    print(f"Connected to mock device on port: {device.portstr}")
    measurement_active = False
    try:
        while True:
            cmd = input("Enter command to send to device (or 'exit' to quit): ")
            if cmd.lower() == "exit":
                break
            device.write((cmd + "\n").encode("utf-8"))
            time.sleep(0.1)
            if cmd.lower() == "s1":
                measurement_active = True
                print("Measurement started.")
                while True:
                    response = device.read(5)
                    print(response)
            elif cmd.lower() == "s0":
                measurement_active = False
                print("Measurement stopped.")
            if device.in_waiting > 0:
                if measurement_active:
                    print("Reading data from device...")
                    response = device.read(5)
                # Read response from the device
                else:
                    response = device.readline().decode("utf-8").strip()
                print(f"Device response: {response}")
    finally:
        device.close()


if __name__ == "__main__":
    main()
