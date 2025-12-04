"""Device management for line-based (CSV) streaming data acquisition via UDP."""

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
)

# Relative imports für installiertes Package, absolute für lokale Ausführung
try:
    from .debug_utils import Debug
except ImportError:
    from debug_utils import Debug


class DataAcquisitionThread(QThread):
    """QThread reading line-based CSV data over UDP.

    Provides both a single-value signal and a multi-value signal
    (elapsed_time_sec, frequency, accel_z, gyro_z). The elapsed time is
    derived from the 'Current Time' column of the incoming stream.
    Frequency is now directly provided in the data stream.
    """

    # First argument now: elapsed time in seconds (float) based on 'Current Time'
    data_point = Signal(float, float)
    multi_data_point = Signal(float, float, float, float)
    connection_lost = Signal()  # New signal for connection loss detection

    DEFAULT_PRIMARY_FIELD = "accel_magnitude"
    DEFAULT_HEADER_BASIC = [
        "Current Time",
        "Frequency",
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
        self._skip_first_point = False  # Flag to discard first point after reset

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
        Debug.info("CSV acquisition thread started (UDP mode)")
        sock = self.manager.connection
        if not sock:
            Debug.error("No active socket – thread exits.")
            return
        sock.settimeout(0.1)
        while self._running and not self.isInterruptionRequested():
            if not self.manager.connected:
                time.sleep(0.05)
                continue
            # Check if connection changed (after reconnect)
            if sock != self.manager.connection:
                Debug.debug("Socket changed - updating reference")
                sock = self.manager.connection
                if not sock:
                    time.sleep(0.05)
                    continue
                sock.settimeout(0.1)
            try:
                if sock:  # Ensure sock is not None before using it
                    chunk = self._receive_chunk(sock)
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

    def _receive_chunk(self, sock: socket.socket) -> bytes:
        try:
            # Check if socket is still valid
            if not sock or sock.fileno() == -1:
                return b""

            # For UDP, receive data with address info
            data, addr = sock.recvfrom(4096)

            # Validate received data
            if not data:
                return b""

            # Check for obvious corruption in UDP packet
            try:
                # Try to decode as UTF-8 to catch binary corruption early
                decoded = data.decode("utf-8", errors="strict")

                # Basic sanity check: should contain some CSV-like structure
                if "," not in decoded and len(decoded) > 10:
                    Debug.debug(
                        f"UDP packet doesn't look like CSV data: {decoded[:30]}..."
                    )
                    return b""

                return data
            except UnicodeDecodeError:
                Debug.debug("UDP packet contains invalid UTF-8, skipping")
                return b""

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
            # If buffer is getting too large without newline, it might be corrupted
            if len(self._buffer) > 1000:
                Debug.debug("Buffer too large without newline, clearing")
                self._buffer = ""
            return

        lines = self._buffer.splitlines(keepends=False)  # Split lines
        if not self._buffer.endswith("\n") and lines:
            # Keep the last incomplete line in buffer
            self._buffer = lines[-1]
            lines = lines[:-1]
        else:
            self._buffer = ""

        # Process each complete line
        valid_lines = 0
        for raw in lines:
            line = raw.strip()
            if line:
                # Additional check: skip obviously corrupted lines
                Debug.debug(f"Processing line: {line}...")
                if self._is_line_corrupted(line):
                    Debug.debug(f"Corrupted line skipped: {line[:30]}...")
                    continue

                self._process_line(line)
                valid_lines += 1

        # Log if we're getting many invalid lines
        if len(lines) > 0 and valid_lines == 0:
            Debug.debug(f"All {len(lines)} lines were invalid/corrupted")

    def _is_line_corrupted(self, line: str) -> bool:
        """Check for obvious signs of line corruption."""
        # Check for binary data or control characters
        try:
            line.encode("ascii")
        except UnicodeEncodeError:
            return True

        # Check for too many consecutive identical characters (likely corruption)
        for i in range(len(line) - 5):
            if len(set(line[i : i + 6])) == 1:  # 6 identical chars in a row
                return True

        # Check for unreasonable line length
        if len(line) > 500:  # Too long for normal CSV
            return True

        return False

    def _process_line(self, line: str) -> None:
        # Validate and filter the line before processing
        if not self._validate_line(line):
            Debug.debug(f"Invalid line rejected: {line[:50]}...")
            return

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
            Debug.debug(f"Line too short ({len(parts)} parts): {line[:30]}...")
            return
        self._emit_data(parts)

    def _validate_line(self, line: str) -> bool:
        """Validate that a line contains proper data format."""
        if not line or not line.strip():
            return False

        # Check for minimum length
        if len(line.strip()) < 10:
            return False

        # Must contain commas for CSV format
        if "," not in line:
            return False

        # Split and validate parts
        parts = [p.strip() for p in line.split(",")]

        # Must have reasonable number of parts (at least 6 for basic gyroscope data)
        if len(parts) < 6:
            return False

        # If we already have a header, validate against expected field count
        if self._header_detected and len(parts) != len(self._header):
            Debug.debug(
                f"Field count mismatch: expected {len(self._header)}, got {len(parts)}"
            )
            return False

        # Validate that most parts are numeric (for data lines)
        numeric_count = 0
        for part in parts:
            if self._is_number(part):
                numeric_count += 1

        # For data lines, at least 80% should be numeric
        if numeric_count / len(parts) < 0.8:
            # Could be a header line, which is ok
            if not self._header_detected:
                return True
            else:
                return False

        # Additional validation: check for reasonable value ranges
        if self._header_detected:
            return self._validate_data_ranges(parts)

        return True

    def _validate_data_ranges(self, parts: List[str]) -> bool:
        """Validate that numeric values are within reasonable ranges."""
        try:
            for i, part in enumerate(parts):
                if not self._is_number(part):
                    continue

                value = float(part)

                # Skip timestamp/frequency fields (usually first field)
                if i == 0:
                    continue

                # Check for obviously invalid values
                if abs(value) > 10000:  # Extreme values
                    Debug.debug(f"Value out of range: {value} at position {i}")
                    return False

                # Check for NaN or infinite values
                if not (value == value) or abs(value) == float("inf"):  # NaN check
                    Debug.debug(f"Invalid numeric value: {value} at position {i}")
                    return False

            return True
        except Exception as e:
            Debug.debug(f"Data validation error: {e}")
            return False

    def _maybe_infer_numeric_header(self, parts: List[str]) -> bool:
        if not parts:
            return False
        if all(self._is_number(p) for p in parts) and len(parts) >= 8:
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
                value = float(parts[idx])
                return value
            except Exception:
                return None

        # Get frequency directly from the data stream
        frequency = getf("Frequency")
        accel_x = getf("Acceleration X")
        accel_y = getf("Acceleration Y")
        accel_z = getf("Acceleration Z")
        gyro_x = getf("Gyro X")
        gyro_y = getf("Gyro Y")
        gyro_z = getf("Gyro Z")

        # Elapsed time computation from 'Current Time'
        current_time_raw = getf("Current Time")
        if current_time_raw is not None:
            # If this is the first time we see a current_time value since a reset,
            # initialise the time base and explicitly emit elapsed = 0.0 to avoid
            # race conditions where an upstream point appears before the UI
            # has recorded the measurement start.
            if self._time_base_raw is None:
                self._time_base_raw = current_time_raw
                elapsed_sec = 0.0
                raw_delta = 0.0
            else:
                raw_delta = current_time_raw - self._time_base_raw

                # Detect time jumps backwards (e.g., mock server loop restart)
                # If time goes backwards significantly, skip this point
                if raw_delta < 0 or raw_delta < (
                    self._last_elapsed_sec * 1_000.0 - 1000
                ):
                    Debug.debug(
                        f"Time jump detected: raw={current_time_raw}µs, base={self._time_base_raw}µs, "
                        f"delta={raw_delta}µs, last_elapsed={self._last_elapsed_sec:.6f}s - SKIPPING POINT"
                    )
                    self._index += 1
                    return

                # Ensure raw_delta is non-negative after check
                raw_delta = max(0.0, raw_delta)

                # Arduino sends time in milliseconds - always convert to seconds
                # Fixed conversion: millisekunden / 1_000 = seconds
                elapsed_sec = raw_delta / 1_000.0

            # Debug log for the first few conversions to help diagnose unit/ordering issues
            try:
                dbg_count = getattr(self, "_time_debug_count", 0)
                if dbg_count < 12:
                    Debug.debug(
                        f"Time conversion idx={self._index}: raw={current_time_raw}µs, base={self._time_base_raw}µs, delta={raw_delta}µs, elapsed={elapsed_sec:.6f}s, last_elapsed={self._last_elapsed_sec:.6f}s"
                    )
                    self._time_debug_count = dbg_count + 1
            except Exception:
                # Defensive: don't let debug formatting break acquisition
                pass
        else:
            # Fallback: synthesize from internal counter (legacy)
            elapsed_sec = float(self._index)
        self._last_elapsed_sec = elapsed_sec

        # Discard the very first point after a reset to avoid displaying old values
        if self._skip_first_point:
            Debug.debug(
                f"Discarding first point after reset: elapsed={elapsed_sec:.6f}s, freq={frequency}, gyro_z={gyro_z}"
            )
            self._skip_first_point = False
            self._index += 1
            return

        # Primary value is frequency if available, otherwise accel_z, then gyro_z
        primary = (
            frequency
            if frequency is not None
            else (accel_z if accel_z is not None else gyro_z)
        )
        if primary is None:
            return

        self.data_point.emit(float(elapsed_sec), float(primary))

        # Send all 8 data values but only pass specific ones to plots
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
        Debug.debug(
            "DataAcquisitionThread.reset_index() called - clearing time base and counters"
        )
        self._index = 0
        self._time_base_raw = None
        self._last_elapsed_sec = 0.0
        self._skip_first_point = True  # Discard the very first point after reset

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
        self.server_address: Optional[tuple] = None  # For UDP server address
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

    def _get_local_ip_for_server(self, server_host: str) -> str:
        """Get the local IP address that will be used to connect to the server."""
        try:
            # Create a dummy socket to determine which local IP would be used
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as temp_socket:
                # Connect to the server (doesn't actually send data for UDP)
                temp_socket.connect((server_host, 80))  # Port doesn't matter for this
                local_ip = temp_socket.getsockname()[0]
                Debug.debug(f"Local IP for server {server_host}: {local_ip}")
                return local_ip
        except Exception as e:
            Debug.debug(f"Could not determine local IP: {e}, using fallback")
            # Fallback: try to get any available IP
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                return local_ip
            except Exception:
                # Last resort: return localhost
                return "127.0.0.1"

    def connect_device(self, ip: str, timeout: float) -> bool:
        """Connect via UDP to the device with unicast handshake."""
        host, port = self._parse_host_port(ip)
        try:
            Debug.debug(
                f"Attempting to connect via UDP to {host}:{port} with timeout {timeout}"
            )

            # Create UDP socket and bind to same port to receive unicast data
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.connection.settimeout(timeout)

            # Bind to the same port as the server to receive unicast data
            try:
                self.connection.bind(("", port))
                Debug.debug(f"Client bound to port {port} for unicast reception")
            except OSError as e:
                # If port is busy, wait a bit and try again
                Debug.debug(f"Port {port} busy ({e}), waiting and retrying...")
                time.sleep(0.2)
                try:
                    self.connection.bind(("", port))
                    Debug.debug(
                        f"Client bound to port {port} for unicast reception (retry successful)"
                    )
                except OSError as e2:
                    # If still busy, try auto-assignment
                    Debug.debug(
                        f"Could not bind to port {port} after retry: {e2}, trying auto-assignment"
                    )
                    self.connection.bind(("", 0))  # Let OS assign a port
                    bound_port = self.connection.getsockname()[1]
                    Debug.debug(f"Client bound to auto-assigned port {bound_port}")

            # Store server address for later use
            self.server_address = (host, port)

            # Get local IP address that will be used to reach the server
            client_ip = self._get_local_ip_for_server(host)
            client_port = self.connection.getsockname()[1]

            # Send connect signal to inform server about unicast client
            Debug.debug(f"Sending connect signal from {client_ip}:{client_port}")
            connect_msg = f"CONNECT:{client_ip}:{client_port}".encode("utf-8")
            self.connection.sendto(connect_msg, self.server_address)

            # Test connection by waiting for actual data
            Debug.debug("Waiting for data to verify connection...")
            data_received = False
            test_start_time = time.time()
            test_timeout = min(timeout, 3.0)  # Maximum 3 seconds for data test

            while time.time() - test_start_time < test_timeout:
                try:
                    # Try to receive data with short timeout
                    self.connection.settimeout(0.5)
                    data, addr = self.connection.recvfrom(4096)
                    if data:
                        Debug.debug(f"Data received from {addr}: {len(data)} bytes")
                        data_received = True
                        break
                except socket.timeout:
                    continue
                except Exception as e:
                    Debug.debug(f"Error during data test: {e}")
                    break

            # Reset socket timeout for normal operation
            self.connection.settimeout(timeout)

            if not data_received:
                Debug.error("No data received - connection test failed")
                self.connection.close()
                self.connection = None
                if self.status_callback:
                    self.status_callback(
                        "UDP connection test failed - no data received", "red"
                    )
                return False

            # Connection established and verified with data
            self.connected = True
            # Store connection params for reconnection
            self.last_connection_params = (ip, timeout)
            self.reconnect_attempts = 0  # Reset reconnect counter
            if self.status_callback:
                self.status_callback(
                    f"Connected via UDP unicast to {host}:{port} (listening on {client_port})",
                    "green",
                )
            # Emit signal for successful connection
            self.connection_successful.emit()
            return True

        except Exception as e:  # pragma: no cover - network dependent
            Debug.error("UDP connection failed", e)
            self.connected = False
            if self.status_callback:
                self.status_callback(f"UDP connection failed: {e}", "red")
            return False

    def _parse_host_port(self, ip: str) -> Tuple[str, int]:
        """Parse host:port from a string. Supports forms like 'host:port', 'http://host:port', '[ipv6]:port'."""
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
            f"Attempting UDP reconnection to {ip} (attempt {self.reconnect_attempts}) - will send new connect signal"
        )

        # Close old connection if it exists
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None

        # Try to reconnect (this will automatically send a new connect signal)
        if self.connect_device(ip, timeout):
            Debug.info("UDP reconnection successful - connect signal sent to Arduino")
            if self.status_callback:
                self.status_callback("Reconnected successfully via UDP", "green")
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
