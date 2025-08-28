"""Device management for line-based (CSV) streaming data acquisition."""

from typing import Callable, Optional, Tuple, List
import time
from threading import Event
import socket
from math import nan

from PySide6.QtCore import (
    QThread,
    Signal,
    QObject,
    QTimer,
)  # pylint: disable=no-name-in-module

from src.debug_utils import Debug


class DataAcquisitionThread(QThread):
    """QThread reading line-based CSV data over TCP.

    Provides both a single-value signal and a multi-value signal
    (elapsed_time_sec, frequency, accel_z, gyro_z). The elapsed time is
    derived from the 'Current Time' column of the incoming stream.
    """

    # First argument now: elapsed time in seconds (float) based on 'Current Time'
    data_point = Signal(float, float)
    multi_data_point = Signal(float, float, float, float)
    connection_lost = Signal()  # New signal for connection loss detection

    DEFAULT_PRIMARY_FIELD = "accel_magnitude"
    DEFAULT_HEADER_BASIC = [
        "Current Time",
        "Last Interrupt Time",
        "Second Last Interrupt",
        "Acceleration X",
        "Acceleration Y",
        "Acceleration Z",
        "Gyro X",
        "Gyro Y",
        "Gyro Z",
    ]

    def __init__(self, manager: "DeviceManager") -> None:  # noqa: F821
        super().__init__()
        self.manager = manager
        self._running = False

        self._index = 0  # retained for potential legacy internal use
        self._buffer = ""
        self._header = []
        self._header_detected = False
        self._last_log = time.time()
        self._time_base_raw = None  # raw base of 'Current Time'
        self._last_elapsed_sec = 0.0

        # Connection monitoring
        self._last_data_time = time.time()
        self._data_timeout = 5.0  # 5 seconds without data = connection lost
        self._connection_lost_emitted = False

    def _parse_header(self, line: str) -> bool:
        """Check if the line contains a valid header.

        Args:
            line (str): The line to parse.

        Returns:
            bool: True if the line contains a valid header, False otherwise.
        """
        raw_line = line.strip().lower()
        if not raw_line:
            return False

        meta_keywords = [
            "content-type",
            "cache-control",
            "pragma",
            "expires",
            "transfer-encoding",
            "connection:",
            "server:",
            "http/1.1",
        ]
        # Check for http meta keywords
        if any(k in raw_line for k in meta_keywords):
            return False

        parts = [f.strip() for f in raw_line.split(",") if f.strip()]
        if len(parts) < 3:  # Not enough parts
            return False
        if all(self._is_number(p) for p in parts):  # All parts are numbers
            return False
        if any(":" in p for p in parts):  # Check for key-value pairs
            return False
        # Check for valid header parts
        expected = [x.lower() for x in self.DEFAULT_HEADER_BASIC.copy()]
        matches = sum(1 for p in parts if p in expected)  # Count matches
        if matches == 0 or matches < len(parts) / 3:
            return False
        self._header = parts  # Store the detected header
        self._header_detected = True
        Debug.info(f"Header detected: {self._header}")
        return True

    @staticmethod
    def _is_number(token: str) -> bool:
        """Check if a string can be converted to a float."""
        try:
            float(token)
            return True
        except ValueError:
            return False

    # ---------------- Main loop -----------------
    def run(self) -> None:  # noqa: D401
        self._running = True
        Debug.info("CSV acquisition thread started (TCP line mode)")
        conn = self.manager.connection
        if not conn:
            Debug.error("No active socket – thread exits.")
            return
        conn.settimeout(0.1)
        while self._running and not self.isInterruptionRequested():
            if not self.manager.connected:
                time.sleep(0.05)
                continue
            # Check if connection changed (after reconnect)
            if conn != self.manager.connection:
                Debug.debug("Socket changed - updating reference")
                conn = self.manager.connection
                if not conn:
                    time.sleep(0.05)
                    continue
                conn.settimeout(0.1)
            try:
                if conn:  # Ensure conn is not None before using it
                    chunk = self._receive_chunk(conn)
                    if chunk:
                        self._buffer += chunk.decode("utf-8", errors="ignore")
                        # Reset connection monitoring when data is received
                        self._last_data_time = time.time()
                        self._connection_lost_emitted = False
                else:
                    time.sleep(0.05)
                    continue
                self._process_buffer()
                self._check_connection_timeout()
                self._periodic_log()
            except Exception as exc:  # pragma: no cover
                Debug.error(f"CSV acquisition error: {exc}")
                time.sleep(0.01)
        Debug.info("CSV acquisition thread stopped")

    def _receive_chunk(self, conn: socket.socket) -> bytes:
        try:
            # Check if socket is still valid
            if not conn or conn.fileno() == -1:
                return b""
            return conn.recv(4096)
        except socket.timeout:
            return b""
        except (OSError, socket.error) as e:  # Handle socket errors more specifically
            if hasattr(e, "errno") and e.errno in (
                9,
                104,
                110,
            ):  # Bad file descriptor, Connection reset, Connection timed out
                Debug.debug(f"Socket disconnected: {e}")
                return b""
            Debug.error(f"Socket error: {e}")
            time.sleep(0.05)
            return b""

    def _check_connection_timeout(self) -> None:
        """Check if no data has been received for too long and emit connection lost signal."""
        current_time = time.time()
        if (
            current_time - self._last_data_time > self._data_timeout
            and not self._connection_lost_emitted
            and self.manager.connected
        ):
            Debug.error(f"No data received for {self._data_timeout}s - connection lost")
            self._connection_lost_emitted = True
            self.connection_lost.emit()

    def _process_buffer(self) -> None:
        # Check if buffer contains at least one complete line
        if "\n" not in self._buffer:
            return
        lines = self._buffer.splitlines(keepends=False)  # Split lines
        if not self._buffer.endswith("\n") and lines:
            self._buffer = lines[-1]
            lines = lines[:-1]
        else:
            self._buffer = ""
        for raw in lines:
            line = raw.strip()
            if line:
                self._process_line(line)

    def _process_line(self, line: str) -> None:
        if not self._header_detected:
            if self._parse_header(line):
                return
            parts = [p.strip() for p in line.split(",")]
            if self._maybe_infer_numeric_header(parts):
                pass
            else:
                return
        else:
            parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            return
        self._emit_data(parts)

    def _maybe_infer_numeric_header(self, parts: List[str]) -> bool:
        if not parts:
            return False
        if all(self._is_number(p) for p in parts) and len(parts) >= 9:
            self._header = self.DEFAULT_HEADER_BASIC[: len(parts)]
            self._header_detected = True
            Debug.info(f"Header fallback inferred (numeric): {self._header}")
            return True
        return False

    def _emit_data(self, parts: List[str]) -> None:
        header_map = {n.lower(): i for i, n in enumerate(self._header)}

        def getf(name: str) -> Optional[float]:
            idx = header_map.get(name.lower())
            if idx is None or idx >= len(parts):
                return None
            try:
                return float(parts[idx])
            except Exception:
                return None

        last_interrupt = getf("Last Interrupt Time") or getf("Last Interrupt")
        second_last = getf("Second Last Interrupt") or getf("SecondLast Interrupt")
        accel_z = getf("Acceleration Z")
        gyro_z = getf("Gyro Z")

        frequency: Optional[float] = None
        if last_interrupt is not None and second_last is not None:
            delta = last_interrupt - second_last
            if delta and delta > 0:
                frequency = 1_000_000.0 / delta

        # Elapsed time computation from 'Current Time'
        current_time_raw = getf("Current Time")
        if current_time_raw is not None:
            if self._time_base_raw is None:
                self._time_base_raw = current_time_raw
            raw_delta = max(0.0, current_time_raw - self._time_base_raw)
            # Assume microseconds if large value, milliseconds if medium
            if raw_delta > 1e6:  # improbable for first delta, safeguard
                elapsed_sec = raw_delta / 1_000_000.0
            elif raw_delta > 1e5:  # >0.1s in microseconds scale
                elapsed_sec = raw_delta / 1_000_000.0
            elif raw_delta > 1e3 and raw_delta < 5e5:
                # Likely milliseconds
                elapsed_sec = raw_delta / 1_000.0
            else:
                # Already seconds
                elapsed_sec = raw_delta
        else:
            # Fallback: synthesize from internal counter (legacy)
            elapsed_sec = float(self._index)
        self._last_elapsed_sec = elapsed_sec

        primary = (
            frequency
            if frequency is not None
            else (accel_z if accel_z is not None else gyro_z)
        )
        if primary is None:
            return
        self.data_point.emit(float(elapsed_sec), float(primary))

        self.multi_data_point.emit(
            float(elapsed_sec),
            float(frequency) if frequency is not None else nan,
            float(accel_z) if accel_z is not None else nan,
            float(gyro_z) if gyro_z is not None else nan,
        )
        self._index += 1  # still increment for potential fallback use

    def _periodic_log(self) -> None:
        """Log the current state every 5 seconds."""
        now = time.time()
        if now - self._last_log > 5.0:
            Debug.debug(
                f"CSV acquisition active: t={self._last_elapsed_sec:.3f}s, lines={self._index}"
            )
            self._last_log = now

    def reset_index(self) -> None:
        """Reset the index and time base for a new measurement."""
        self._index = 0
        self._time_base_raw = None
        self._last_elapsed_sec = 0.0

    def stop(self) -> None:
        """Stop the acquisition thread."""
        self._running = False
        self.requestInterruption()
        self.wait(2000)


class DeviceManager(QObject):
    """Handle device connection and data acquisition."""

    # Signal emitted when connection is successful
    connection_successful = Signal()
    # Signal emitted when connection is lost
    connection_lost = Signal()
    # Signal emitted when attempting reconnection
    reconnection_attempt = Signal(int)  # attempt number

    def __init__(
        self,
        status_callback: Optional[Callable[[str, str], None]] = None,
        data_callback: Optional[Callable[[float, float], None]] = None,
        multi_callback: Optional[Callable[[float, float, float, float], None]] = None,
    ) -> None:
        super().__init__()
        self.status_callback = status_callback
        self.data_callback = data_callback
        self.multi_callback = multi_callback
        self.connected: bool = False
        self.connection: Optional[socket.socket] = None
        self.acquire_thread: Optional[DataAcquisitionThread] = None
        self.stop_event: Event = Event()
        self.measurement_active: bool = False

        # Configuration: selected primary field (header name or 'accel_magnitude')
        self.primary_field_name: str = DataAcquisitionThread.DEFAULT_PRIMARY_FIELD
        # Optional legacy device object (if older hardware API is used)
        self.device = None  # type: ignore[attr-defined]

        # Reconnection settings
        self.last_connection_params = None  # Store (ip, timeout) for reconnection
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self._attempt_reconnection)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 3000  # 3 seconds

    def connect_device(self, ip: str, timeout: float) -> bool:
        """Connect over TCP to the device."""
        host, port = self._parse_host_port(ip)
        try:
            self.connection = socket.create_connection((host, port), timeout=timeout)
            self.connection.settimeout(0.5)  # Short timeout for read ops
            # Try to read a few bytes without assuming a protocol
            try:
                temp = self.connection.recv(32)
                Debug.debug(f"Connected. Received data over TCP: {temp}")
                self.connected = True
                # Store connection params for reconnection
                self.last_connection_params = (ip, timeout)
                self.reconnect_attempts = 0  # Reset reconnect counter
                if self.status_callback:
                    self.status_callback(f"Connected to {port}", "green")
                # Emit signal for successful connection
                self.connection_successful.emit()
            except socket.timeout:
                pass  # No data is also fine
            return True
        except Exception as e:  # pragma: no cover - network dependent
            Debug.error("Connection failed", e)
            self.connected = False
            if self.status_callback:
                self.status_callback(f"Connection failed: {e}", "red")
            return False

    def disconnect_device(self) -> None:
        """Close existing connection and stop acquisition."""
        self.stop_acquisition()
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None
        self.connected = False

    def start_acquisition(self) -> bool:
        """Start or (re)connect the acquisition thread."""
        if self.acquire_thread and self.acquire_thread.isRunning():
            if self.data_callback:
                # Ensure our callback is connected even if the thread was
                # started before the callback was assigned.
                self.acquire_thread.data_point.connect(self.data_callback)
            if self.multi_callback:
                self.acquire_thread.multi_data_point.connect(self.multi_callback)
            return True

        self.acquire_thread = DataAcquisitionThread(self)
        if self.data_callback:
            self.acquire_thread.data_point.connect(self.data_callback)
        if self.multi_callback:
            self.acquire_thread.multi_data_point.connect(self.multi_callback)
        # Connect connection lost signal to our handler
        self.acquire_thread.connection_lost.connect(self._handle_connection_lost)
        self.acquire_thread.start()
        return True

    def stop_acquisition(self) -> bool:
        """Stop the acquisition thread."""
        if self.acquire_thread and self.acquire_thread.isRunning():
            self.acquire_thread.stop()
        self.acquire_thread = None
        return True

    def start_measurement(self) -> bool:
        """Start a measurement session (only toggles saving/statistics).

        Acquisition itself keeps running continuously.
        """
        if not self.connected:
            return False
        try:
            if self.acquire_thread:
                self.acquire_thread.reset_index()
            # Optionally notify legacy device
            if self.device:
                try:
                    self.device.set_counting(True)
                except (AttributeError, RuntimeError, OSError) as e:  # pragma: no cover
                    Debug.error(f"Legacy set_counting failed: {e}")
            self.measurement_active = True
            return True
        except (AttributeError, RuntimeError, OSError) as exc:  # pragma: no cover
            Debug.error(f"Failed to start measurement: {exc}")
            return False

    def stop_measurement(self) -> bool:
        """Stop a measurement session (acquisition continues, only saving off)."""
        if not self.connected:
            self.measurement_active = False
            return False
        try:
            if self.device:
                try:
                    self.device.set_counting(False)
                except (AttributeError, RuntimeError, OSError) as e:  # pragma: no cover
                    Debug.error(f"Legacy set_counting stop failed: {e}")
        except (AttributeError, RuntimeError, OSError) as exc:  # pragma: no cover
            Debug.error(f"Failed to stop measurement: {exc}")
        self.measurement_active = False
        return True

    def _parse_host_port(self, ip: str) -> Tuple[str, int]:
        """Parse host:port from a string.

        Supports forms like 'host:port', 'http://host:port', '[ipv6]:port'.
        """
        ip = ip.strip()
        # Remove scheme
        if "://" in ip:
            ip = ip.split("://", 1)[1]
        # IPv6 wrapped in []
        if ip.startswith("["):
            host, rest = ip.split("]", 1)
            host = host[1:]
            if rest.startswith(":"):
                port = int(rest[1:])
            else:
                port = 80
            return host, port
        # Regular host:port
        if ip.count(":") == 1:
            host, port_s = ip.split(":", 1)
            try:
                port = int(port_s)
            except ValueError:
                port = 80
            return host, port
        # Host only
        return ip, 80

    # ---------------------------------------------------------
    # Configuration API
    # ---------------------------------------------------------
    def set_primary_field(self, field_name: str) -> None:
        """Set the field that should be emitted as single value.

        Examples:
            set_primary_field("Acceleration Z")
            set_primary_field("Gyro Y")
            set_primary_field("accel_magnitude")  # magnitude from X/Y/Z
        """
        self.primary_field_name = field_name
        Debug.info(f"Primary field set: {field_name}")

    def shutdown(self) -> None:
        """Shutdown the manager cleanly (idempotent)."""
        # Stop reconnection timer
        if hasattr(self, "reconnect_timer"):
            self.reconnect_timer.stop()
        try:
            self.stop_acquisition()
        except Exception:  # pragma: no cover
            pass
        try:
            self.disconnect_device()
        except Exception:  # pragma: no cover
            pass
        self.measurement_active = False

    def _handle_connection_lost(self) -> None:
        """Handle connection loss detected by the acquisition thread."""
        Debug.error("Connection lost - starting reconnection process")
        self.connected = False
        if self.status_callback:
            self.status_callback("Connection lost - attempting reconnection...", "red")
        self.connection_lost.emit()

        # Start reconnection process
        if (
            self.last_connection_params
            and self.reconnect_attempts < self.max_reconnect_attempts
        ):
            self.reconnect_attempts += 1
            self.reconnection_attempt.emit(self.reconnect_attempts)
            if self.status_callback:
                self.status_callback(
                    f"Reconnecting... (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})",
                    "orange",
                )
            self.reconnect_timer.start(self.reconnect_delay)
        else:
            if self.status_callback:
                self.status_callback(
                    "Reconnection failed - max attempts reached", "red"
                )

    def _attempt_reconnection(self) -> None:
        """Attempt to reconnect using stored connection parameters."""
        if not self.last_connection_params:
            return

        ip, timeout = self.last_connection_params
        Debug.info(
            f"Attempting reconnection to {ip} (attempt {self.reconnect_attempts})"
        )

        # Close old connection if it exists
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None

        # Try to reconnect
        if self.connect_device(ip, timeout):
            Debug.info("Reconnection successful")
            if self.status_callback:
                self.status_callback("Reconnected successfully", "green")
            # Restart acquisition if it was running
            if self.acquire_thread:
                self.start_acquisition()
        else:
            # Failed to reconnect, try again if we haven't reached max attempts
            if self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                self.reconnection_attempt.emit(self.reconnect_attempts)
                if self.status_callback:
                    self.status_callback(
                        f"Reconnecting... (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})",
                        "orange",
                    )
                self.reconnect_timer.start(self.reconnect_delay)
            else:
                if self.status_callback:
                    self.status_callback(
                        "Reconnection failed - max attempts reached", "red"
                    )
