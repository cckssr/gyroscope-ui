"""Loopback fake of the Kreisel firmware (PROTOCOL.md sections 3 to 6) for the adapter tests.

A UDP socket on 127.0.0.1 (ephemeral port) plus an optional tiny HTTP server answering
``GET /info``. Clients register like the real firmware: version 1 remembers the source IP and
always sends to ``data_port``; version 2 parses ``CONNECT:<ip>:<port>``. Data lines come from
``GyroSimulation.line_at``.
"""

from __future__ import annotations

import dataclasses
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from gyroscope_ui.core.simulation import GyroSimulation, SimulationParams

LOCALHOST = "127.0.0.1"


def free_udp_port() -> int:
    """An unused UDP port on 127.0.0.1 (released again; small race window, fine for tests)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((LOCALHOST, 0))
        return int(sock.getsockname()[1])


class _InfoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        fake: FakeFirmware = self.server.fake  # type: ignore[attr-defined]
        body = fake.info_text().encode() if self.path == "/info" else b"0,0.0000,0,0,0,0,0,0\r\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        pass


class FakeFirmware:
    """Firmware v1 or v2 on loopback; use as a context manager."""

    def __init__(
        self,
        protocol_version: int = 1,
        rate_hz: float = 200.0,
        data_port: int = 12345,
        http: bool = True,
        *,
        device_id: str = "E35433",
        software_version: str = "1.1.1",
        params: SimulationParams | None = None,
    ) -> None:
        self.protocol_version = protocol_version
        self.rate_hz = rate_hz
        self.data_port = data_port
        self.device_id = device_id
        self.software_version = software_version
        base = params if params is not None else SimulationParams()
        self._sim = GyroSimulation(
            dataclasses.replace(base, protocol_version=protocol_version, rate_hz=rate_hz)
        )
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((LOCALHOST, 0))
        self._sock.settimeout(0.002)
        self.port: int = self._sock.getsockname()[1]
        self._lock = threading.Lock()
        self._clients: set[tuple[str, int]] = set()
        self._sending = True
        self._registrations = 0
        self._sent = 0
        self._seq = 0
        self._origin_s = 0.0
        self._next_index = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="fake-firmware", daemon=True)
        self._http: ThreadingHTTPServer | None = None
        self._http_thread: threading.Thread | None = None
        if http:
            self._http = ThreadingHTTPServer((LOCALHOST, 0), _InfoHandler)
            self._http.fake = self  # type: ignore[attr-defined]
            self._http_thread = threading.Thread(
                target=self._http.serve_forever, name="fake-firmware-http", daemon=True
            )

    # ---- lifecycle ----------------------------------------------------------------------
    def start(self) -> None:
        self._origin_s = time.monotonic()
        self._thread.start()
        if self._http_thread is not None:
            self._http_thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(2.0)
        if self._http is not None:
            if self._http_thread is not None and self._http_thread.is_alive():
                self._http.shutdown()
                self._http_thread.join(2.0)
            self._http.server_close()
        self._sock.close()

    def __enter__(self) -> FakeFirmware:
        self.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.stop()

    # ---- observation and controls -------------------------------------------------------
    @property
    def http_port(self) -> int:
        """Port of the HTTP server (0 when the fake was created with ``http=False``)."""
        return int(self._http.server_address[1]) if self._http is not None else 0

    @property
    def registrations(self) -> int:
        """Registration datagrams received so far (keep-alives included)."""
        with self._lock:
            return self._registrations

    @property
    def sent(self) -> int:
        """Data datagrams sent so far."""
        with self._lock:
            return self._sent

    def wait_for_registrations(self, count: int = 1, timeout_s: float = 3.0) -> bool:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.registrations >= count:
                return True
            time.sleep(0.005)
        return False

    def stop_sending(self) -> None:
        with self._lock:
            self._sending = False

    def resume(self) -> None:
        with self._lock:
            self._sending = True

    def restart_clock(self) -> None:
        """Reboot of the device: ``millis`` starts at 0 again (the sequence number goes on)."""
        with self._lock:
            self._origin_s = time.monotonic()
            self._next_index = 0

    def send_raw(self, payload: bytes) -> None:
        """Send ``payload`` as one datagram to every registered client."""
        with self._lock:
            targets = list(self._clients)
        for target in targets:
            self._sock.sendto(payload, target)

    def info_text(self) -> str:
        lines = [
            f"Device-ID: {self.device_id}",
            f"Software-Version: {self.software_version}",
            "Uptime: 123456 ms",
            "WiFi-Status: Verbunden",
            f"IP-Adresse: {LOCALHOST}",
            "Debug-Modus: Aus",
        ]
        if self.protocol_version >= 2:
            lines.append(f"Protocol: {self.protocol_version}")
        return "\n".join(lines) + "\n"

    # ---- thread -------------------------------------------------------------------------
    def _register(self, payload: bytes, source: tuple[str, int]) -> None:
        client = (source[0], self.data_port)
        if self.protocol_version >= 2:
            client = source  # malformed payload: source IP and source port
            text = payload.decode("ascii", errors="replace")
            if text.startswith("CONNECT:"):
                ip, _, port = text[len("CONNECT:") :].rpartition(":")
                if ip and port.isdigit():
                    client = (ip, int(port))
        with self._lock:
            self._registrations += 1
            self._clients.add(client)

    def _send_due(self) -> None:
        with self._lock:
            due = int((time.monotonic() - self._origin_s) * self.rate_hz)
            if not self._clients or not self._sending:
                self._next_index = due + 1  # silent period: nothing to catch up later
                return
            targets = list(self._clients)
            lines: list[bytes] = []
            while self._next_index <= due:
                t_s = self._next_index / self.rate_hz
                seq = self._seq if self.protocol_version >= 2 else None
                lines.append(self._sim.line_at(t_s, seq).encode("ascii"))
                self._next_index += 1
                self._seq = (self._seq + 1) % 2**32
            self._sent += len(lines)
        for line in lines:
            for target in targets:
                self._sock.sendto(line, target)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                payload, source = self._sock.recvfrom(1024)
            except TimeoutError:
                pass
            except OSError:
                break
            else:
                self._register(payload, source)
            self._send_due()
