import random
import time
import threading
import serial

class SimulatedSerialDevice:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.running = False

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._generate_data)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def _generate_data(self):
        with serial.Serial(self.port, self.baudrate) as ser:
            while self.running:
                number = random.randint(0, 100)
                ser.write(f"{number}\n".encode())
                time.sleep(random.uniform(0.5, 2.0))

def read_serial_data(port, baudrate):
    with serial.Serial(port, baudrate) as ser:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode().strip()
                print(f"Received: {line}")

# Example usage:
# device = SimulatedSerialDevice('/dev/ttyUSB0', 9600)
# device.start()
# read_serial_data('/dev/ttyUSB0', 9600)