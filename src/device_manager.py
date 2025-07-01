"""Device management with threaded acquisition for reuse."""

from typing import Callable, Optional
import time
from threading import Event

from PySide6.QtCore import QThread, Signal  # pylint: disable=no-name-in-module

from src.arduino import GMCounter
from src.debug_utils import Debug


class DataAcquisitionThread(QThread):
    """Background thread that pulls data from the device."""

    data_point = Signal(int, float)

    def __init__(self, manager: "DeviceManager") -> None:
        super().__init__()
        self.manager = manager
        self._running = False
        self._index = 0  # Index-Zähler für Datenpunkte

    def run(self) -> None:
        self._running = True
        Debug.info(
            "Acquisition thread started with binary data acquisition mode (0xAA + 4 bytes + 0x55)"
        )

        # Buffer für binäre Datenpackete
        byte_buffer = b""
        last_process_time = time.time()
        START_BYTE = 0xAA
        END_BYTE = 0x55
        PACKET_SIZE = 6  # 1 Start-Byte + 4 Daten-Bytes + 1 End-Byte

        while self._running and not self.isInterruptionRequested():
            try:
                if not (self.manager.device and self.manager.connected):
                    time.sleep(0.01)  # Reduziert von 0.1s
                    continue

                if not self.manager.measurement_active:
                    time.sleep(0.01)  # Reduziert von 0.1s
                    continue

                # Verwende read_bytes_fast für hochfrequente binäre Datenerfassung
                current_time = time.time()

                # Lese Daten mit read_bytes_fast (größerer Buffer, reduzierter Timeout)
                raw_data = self.manager.device.read_bytes_fast(
                    max_bytes=4096,
                    timeout_ms=1,
                    start_byte=None,  # Optimiert für Geschwindigkeit
                )

                if raw_data:
                    # Füge neue Daten zum Buffer hinzu
                    byte_buffer += raw_data

                    # Verarbeite alle vollständigen 6-Byte-Pakete im Buffer
                    while len(byte_buffer) >= PACKET_SIZE:
                        # Suche nach Start-Byte
                        start_pos = byte_buffer.find(START_BYTE)

                        if start_pos == -1:
                            # Kein Start-Byte gefunden, Buffer leeren
                            byte_buffer = b""
                            Debug.debug(
                                "No START_BYTE found in buffer, clearing buffer"
                            )
                            break

                        if start_pos > 0:
                            # Start-Byte nicht am Anfang, entferne Daten davor
                            Debug.debug(
                                f"START_BYTE not at beginning, removing {start_pos} bytes"
                            )
                            byte_buffer = byte_buffer[start_pos:]
                            continue

                        # Prüfe ob vollständiges Paket vorhanden
                        if len(byte_buffer) >= PACKET_SIZE:
                            # Extrahiere 6-Byte-Paket
                            packet = byte_buffer[:PACKET_SIZE]
                            byte_buffer = byte_buffer[PACKET_SIZE:]

                            # Validiere Start-Byte und End-Byte
                            if packet[0] == START_BYTE and packet[5] == END_BYTE:
                                try:
                                    # Konvertiere 4 Daten-Bytes zu 32-bit unsigned integer (little-endian)
                                    value_bytes = packet[1:5]
                                    value = int.from_bytes(
                                        value_bytes, byteorder="little", signed=False
                                    )

                                    # Emit als float für Kompatibilität
                                    self.data_point.emit(self._index, float(value))
                                    self._index += 1

                                    Debug.debug(
                                        f"Valid packet: 0x{packet.hex()} -> value: {value}"
                                    )

                                except Exception as e:
                                    Debug.error(
                                        f"Error processing valid packet 0x{packet.hex()}: {e}"
                                    )
                                    continue
                            else:
                                # Ungültiges Paket (falsches Start- oder End-Byte)
                                if packet[0] != START_BYTE:
                                    Debug.debug(
                                        f"Invalid START_BYTE in packet: 0x{packet.hex()}"
                                    )
                                if packet[5] != END_BYTE:
                                    Debug.debug(
                                        f"Invalid END_BYTE in packet: 0x{packet.hex()}"
                                    )

                                # Entferne nur das erste Byte und versuche erneut
                                byte_buffer = packet[1:] + byte_buffer
                                continue
                        else:
                            # Nicht genug Daten für vollständiges Paket
                            break

                # Adaptive Pause: Kein Sleep wenn Daten verarbeitet wurden
                if raw_data:
                    # Keine Pause bei aktiven Daten für maximale Geschwindigkeit
                    pass
                else:
                    # Kurze Pause nur wenn keine Daten verfügbar
                    time.sleep(0.001)  # 1ms statt 0.5ms

                # Performance-Logging alle 5 Sekunden
                if current_time - last_process_time > 5.0:
                    buffer_size = len(byte_buffer)
                    Debug.debug(
                        f"Binary acquisition active, processed {self._index} packets, buffer: {buffer_size} bytes"
                    )
                    last_process_time = current_time

            except Exception as exc:
                Debug.error(f"Binary acquisition error: {exc}")
                time.sleep(0.05)  # Kürzere Pause bei Fehlern für binäre Daten

        Debug.info("Binary acquisition thread stopped")

    def reset_index(self) -> None:
        """Reset the data point index counter for a new measurement."""
        self._index = 0
        Debug.debug("Data acquisition index reset to 0")

    def stop(self) -> None:
        self._running = False
        self.requestInterruption()
        self.wait(2000)


class DeviceManager:
    """Handle device connections and data acquisition."""

    def __init__(
        self,
        status_callback: Optional[Callable[[str, str], None]] = None,
        data_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        self.status_callback = status_callback
        self.data_callback = data_callback
        self.connected = False
        self.port = "None"
        self.device: Optional[GMCounter] = None
        self.acquire_thread: Optional[DataAcquisitionThread] = None
        self.stop_event = Event()
        self.measurement_active = False

    def connect(self, port: str, baudrate: int) -> bool:
        """Connect to the given serial port."""
        self.port = port
        self.disconnect()
        try:
            self.device = GMCounter(port=port, baudrate=baudrate)
            self.connected = True
            if self.status_callback:
                self.status_callback(f"Connected to {port}", "green")
            self.start_acquisition()
            return True
        except Exception as exc:
            Debug.error(f"Connection failed: {exc}")
            self.connected = False
            if self.status_callback:
                self.status_callback(f"Connection failed: {exc}", "red")
            return False

    def disconnect(self) -> None:
        """Close existing connection and stop acquisition."""
        self.stop_acquisition()
        if self.device:
            try:
                self.device.close()
            except Exception as exc:  # pragma: no cover - close errors
                Debug.error(f"Error closing device: {exc}")
        self.device = None
        self.connected = False

    def start_acquisition(self) -> bool:
        """Start or (re)connect the acquisition thread."""
        if self.acquire_thread and self.acquire_thread.isRunning():
            if self.data_callback:
                # Ensure our callback is connected even if the thread was
                # started before the callback was assigned.
                self.acquire_thread.data_point.connect(self.data_callback)
            return True

        self.acquire_thread = DataAcquisitionThread(self)
        if self.data_callback:
            self.acquire_thread.data_point.connect(self.data_callback)
        self.acquire_thread.start()
        return True

    def stop_acquisition(self) -> bool:
        """Stop the acquisition thread."""
        if self.acquire_thread and self.acquire_thread.isRunning():
            self.acquire_thread.stop()
        self.acquire_thread = None
        return True

    def start_measurement(self) -> bool:
        """Send start command to device and enable fast acquisition."""
        if not (self.device and self.connected):
            return False
        try:
            # Reset index counter for new measurement
            if self.acquire_thread:
                self.acquire_thread.reset_index()

            self.device.set_counting(True)
            self.measurement_active = True
            return True
        except Exception as exc:  # pragma: no cover - unexpected errors
            Debug.error(f"Failed to start measurement: {exc}")
            return False

    def stop_measurement(self) -> bool:
        """Stop counting and resume configuration polling."""
        if not (self.device and self.connected):
            self.measurement_active = False
            return False
        try:
            self.device.set_counting(False)
        except Exception as exc:  # pragma: no cover - unexpected errors
            Debug.error(f"Failed to stop measurement: {exc}")
        self.measurement_active = False
        return True
