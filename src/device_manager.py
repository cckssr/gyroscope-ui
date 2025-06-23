"""Device management with threaded acquisition for reuse."""

from typing import Callable, Optional
import time
from threading import Event

from PySide6.QtCore import QThread, Signal

from src.arduino import GMCounter
from src.debug_utils import Debug


class DataAcquisitionThread(QThread):
    """Background thread that pulls data from the device."""

    data_point = Signal(int, float)

    def __init__(self, manager: "DeviceManager") -> None:
        super().__init__()
        self.manager = manager
        self._running = False

    def run(self) -> None:
        self._running = True
        index = 0
        Debug.info("Acquisition thread started")
        while self._running and not self.isInterruptionRequested():
            try:
                if self.manager.device and self.manager.connected:
                    if self.manager.measurement_active:
                        line = self.manager.device.read_value()
                        if line is None:
                            continue
                        try:
                            value = float(line)
                        except ValueError:
                            # Probably measurement stopped, switch mode
                            self.manager.measurement_active = False
                            continue
                        self.data_point.emit(index, value)
                        index += 1
                    else:
                        data = self.manager.device.get_data(True)
                        if data and isinstance(data, dict):
                            value = data.get("count")
                            if value is not None:
                                self.data_point.emit(index, float(value))
                                index += 1
                        time.sleep(1)
                else:
                    time.sleep(0.1)
            except Exception as exc:  # pragma: no cover - unexpected errors
                Debug.error(f"Acquisition error: {exc}")
                time.sleep(0.5)
        Debug.info("Acquisition thread stopped")

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

    def connect(self, port: str) -> bool:
        """Connect to the given serial port."""
        self.port = port
        self.disconnect()
        try:
            self.device = GMCounter(port=port)
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
        """Start the acquisition thread using QThread."""
        if self.acquire_thread and self.acquire_thread.isRunning():
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
