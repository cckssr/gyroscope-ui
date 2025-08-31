#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock Arduino WiFi Daten-Streamer (UDP)
======================================

Dieses Skript emuliert das Verhalten des Arduino-Sketches über UDP.
Es startet einen UDP-Server und sendet kontinuierlich Sensordaten-Pakete
im CSV-Format. Die Daten basieren auf der Datei `tests/mock_daten_ext.csv`
und werden in einer Endlosschleife abgespielt.

Neues Format (8 Datenfelder entsprechend UDP-Implementierung):
    Current Time, Frequency, Acceleration X, Acceleration Y, Acceleration Z,
    Gyro X, Gyro Y, Gyro Z

Nutzung:
    python scripts/mock_arduino_server.py --port 8080 --rate 100

Der Server sendet UDP-Pakete an alle verbundenen Clients (UDP ist connectionless).

Argumente:
    --port / -p        UDP-Port (Default 8080)
    --host             Bind-Adresse (Default 0.0.0.0 für alle Interfaces)
    --rate / -r        Pakete pro Sekunde (Default 100 → ca. 10 ms Interval)
    --file / -f        Pfad zu CSV (Default tests/mock_daten_ext.csv)
    --jitter           Zufälliges zeitliches Jitter (ms) ± (Default 0)
    --noise            Kleine zufällige Rausch-Amplitude für float-Spalten (Default 0.0)
    --no-loop          Höre nach einmaligem Durchlauf auf (Standard: Endlosschleife)
    --target-host      Ziel-Host für UDP-Pakete (Default: sendet an letzten Empfänger)
    --target-port      Ziel-Port für UDP-Pakete (Default: sendet an letzten Empfänger)

Hinweis: Der Server bindet standardmäßig an alle Interfaces (0.0.0.0) für
externe Erreichbarkeit. Verwende --host 127.0.0.1 für nur lokale Verbindungen.

Abbruch mit Ctrl+C.
"""
from __future__ import annotations

import argparse
import csv
import random
import signal
import socket
import sys
import threading
import time
import numpy as np
from dataclasses import dataclass
from tempfile import gettempdir
import os
from pathlib import Path
from typing import List, Optional

STOP_EVENT = threading.Event()
RUN_MARKER_PATH: str | None = None  # Pfad zur Marker-Datei


def handle_sigint(_signum, _frame):  # noqa: D401
    """Signal-Handler für Ctrl+C."""
    STOP_EVENT.set()
    print("\n[MockArduino] Stop signal empfangen – fahre herunter...", flush=True)


signal.signal(signal.SIGINT, handle_sigint)


@dataclass
class DataRow:
    current_time: int
    frequency: float
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float

    def to_csv_udp(self) -> str:
        """Format für UDP: 8 Werte entsprechend dem neuen Header-Format."""
        return f"{self.current_time},{self.frequency:.2f},{self.ax:.2f},{self.ay:.2f},{self.az:.2f},{self.gx:.2f},{self.gy:.2f},{self.gz:.2f}\n"

    def to_csv_basic(self) -> str:
        """Legacy-Format für Rückwärtskompatibilität."""
        # Simuliere interrupt-basierte Felder basierend auf Frequenz
        if self.frequency > 0:
            period_us = int(1000000 / self.frequency)
            last_interrupt = self.current_time - period_us
            second_last_interrupt = last_interrupt - period_us
        else:
            last_interrupt = self.current_time - 10000
            second_last_interrupt = self.current_time - 20000
        return f"{self.current_time},{last_interrupt},{second_last_interrupt},{self.ax:.2f},{self.ay:.2f},{self.az:.2f},{self.gx:.2f},{self.gy:.2f},{self.gz:.2f}"

    def to_csv_extended(self) -> str:
        """Legacy erweiterte Format."""
        basic = self.to_csv_basic()
        return f"{basic},{self.ax:.2f},{self.ay:.2f},{self.az:.2f},{self.gx:.2f},{self.gy:.2f},{self.gz:.2f}"


class gyro_simulator:
    def __init__(self, data: List[DataRow]):
        self.data = data
        self.index = 0
        self.last_acc = 0

    def get_next(self) -> DataRow | None:
        if self.index < len(self.data):
            row = self.data[self.index]
            self.index += 1
            return row
        return None

    def frequency(self, t, f0, mu):
        return f0 - mu * t

    def gyro(self, t, g0, omega, mu):
        return g0 * np.sin(omega * t) * np.exp(-mu * t)


def load_data(path: Path) -> List[DataRow]:
    if not path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")

    rows: List[DataRow] = []

    # Check if this is the extended format file (neue UDP-Format)
    if "mock_daten_ext.csv" in str(path):
        return load_data_extended(path)

    # Original format loading (Legacy-Unterstützung)
    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        # Erkennen ob Header-Zeile vorhanden ist (prüfe auf nicht-numerische Tokens)
        if header and any(
            not token.replace("-", "").replace(".", "").isdigit() for token in header
        ):
            # header already consumed
            pass
        else:
            # Erste Zeile war schon Daten
            if header:
                try:
                    values = [float(x) for x in header]
                    if len(values) >= 9:
                        # Legacy format: berechne Frequenz aus Interrupt-Zeiten
                        frequency = 0.0
                        if len(values) >= 3 and values[1] != values[2]:
                            delta = values[1] - values[2]
                            if delta > 0:
                                frequency = 1000.0 / delta  # ms to Hz conversion
                        rows.append(
                            DataRow(
                                int(values[0]),
                                frequency,
                                *values[3:9],
                            )
                        )
                except (ValueError, TypeError):
                    pass
        for line in reader:
            if not line:
                continue
            try:
                values = [float(x) for x in line]
                if len(values) < 9:
                    continue
                # Legacy format: berechne Frequenz aus Interrupt-Zeiten
                frequency = 0.0
                if len(values) >= 3 and values[1] != values[2]:
                    delta = values[1] - values[2]
                    if delta > 0:
                        frequency = 1000.0 / delta  # ms to Hz conversion
                rows.append(
                    DataRow(
                        int(values[0]),
                        frequency,
                        float(values[3]),
                        float(values[4]),
                        float(values[5]),
                        float(values[6]),
                        float(values[7]),
                        float(values[8]),
                    )
                )
            except ValueError:
                continue
    if not rows:
        raise ValueError(f"Keine gültigen Datenzeilen in {path} gefunden")
    return rows


def load_data_extended(path: Path) -> List[DataRow]:
    """Load data from mock_daten_ext.csv in new UDP format with frequency directly included."""
    rows: List[DataRow] = []

    # Default values for missing X/Y components
    DEFAULT_CURRENT_TIME = 4525213
    DEFAULT_ACCEL_X = -0.806
    DEFAULT_ACCEL_Y = 1.379
    DEFAULT_GYRO_X = 0.020
    DEFAULT_GYRO_Y = -0.080

    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(
            reader, None
        )  # Skip header: Time (s),Frequency (Hz),Accel Z,Gyro Z

        for line_num, line in enumerate(reader):
            if not line or len(line) < 4:
                continue
            try:
                # Parse: Time (s), Frequency (Hz), Accel Z, Gyro Z
                time_s = float(line[0])
                frequency_hz = float(line[1])
                accel_z = float(line[2])
                gyro_z = float(line[3])

                # Convert time from seconds to microseconds (approximate current_time)
                current_time = int(DEFAULT_CURRENT_TIME + time_s * 1000000)

                rows.append(
                    DataRow(
                        current_time=current_time,
                        frequency=frequency_hz,
                        ax=DEFAULT_ACCEL_X,  # Use average from old file
                        ay=DEFAULT_ACCEL_Y,  # Use average from old file
                        az=accel_z,  # Use value from new file
                        gx=DEFAULT_GYRO_X,  # Use average from old file
                        gy=DEFAULT_GYRO_Y,  # Use average from old file
                        gz=gyro_z,  # Use value from new file
                    )
                )
            except (ValueError, IndexError) as e:
                print(f"Warnung: Zeile {line_num + 2} übersprungen: {e}")
                continue

    if not rows:
        raise ValueError(f"Keine gültigen Datenzeilen in {path} gefunden")

    print(
        f"[MockArduino] {len(rows)} Zeilen aus {path} geladen (UDP-Format mit 8 Feldern)"
    )
    return rows


def apply_noise(row: DataRow, noise_amp: float) -> DataRow:
    if noise_amp <= 0:
        return row
    # Füge leichtes Rauschen auf die Float-Werte hinzu
    return DataRow(
        current_time=row.current_time,
        frequency=row.frequency + random.uniform(-noise_amp, noise_amp),
        ax=row.ax + random.uniform(-noise_amp, noise_amp),
        ay=row.ay + random.uniform(-noise_amp, noise_amp),
        az=row.az + random.uniform(-noise_amp, noise_amp),
        gx=row.gx + random.uniform(-noise_amp, noise_amp),
        gy=row.gy + random.uniform(-noise_amp, noise_amp),
        gz=row.gz + random.uniform(-noise_amp, noise_amp),
    )


def udp_sender_thread(
    sock: socket.socket,
    target_addr: tuple,
    rows: List[DataRow],
    interval_s: float,
    jitter_ms: int,
    noise_amp: float,
    loop: bool,
    follow_timestamps: bool,
    timestamp_scale: float,
):
    """UDP sender thread - sendet kontinuierlich Pakete an Zieladresse."""
    print(f"[MockArduino] UDP-Sender startet, Ziel: {target_addr[0]}:{target_addr[1]}")

    idx = 0
    n = len(rows)
    packet_count = 0

    while not STOP_EVENT.is_set():
        row = rows[idx]
        noisy = apply_noise(row, noise_amp)
        line = noisy.to_csv_udp()  # Verwende das neue UDP-Format

        try:
            packet = line.encode("utf-8")
            sock.sendto(packet, target_addr)
            packet_count += 1

            if packet_count % 1000 == 0:  # Log alle 1000 Pakete
                print(f"[MockArduino] {packet_count} UDP-Pakete gesendet")

        except OSError as e:
            print(f"[MockArduino] UDP-Sendefehler: {e}")
            break

        next_idx = idx + 1
        end_of_cycle = False
        if next_idx >= n:
            if loop:
                next_idx = 0
            else:
                end_of_cycle = True

        # Delay Berechnung
        if follow_timestamps and not end_of_cycle:
            # Nutze Differenz der current_time Felder
            raw_delta = rows[next_idx].current_time - row.current_time
            if raw_delta < 0:
                # Falls Zeit zurückspringt (unerwartet) -> kein Delay
                delay = 0.0
            else:
                # timestamp_scale: z.B. 1000.0 wenn Werte in ms vorliegen
                delay = raw_delta / timestamp_scale
        else:
            delay = interval_s

        if jitter_ms > 0:
            delta = random.uniform(-jitter_ms / 1000.0, jitter_ms / 1000.0)
            delay = max(0.0, delay + delta)
        if delay > 0:
            time.sleep(delay)

        idx = next_idx
        if end_of_cycle:
            if not loop:
                break

    print(f"[MockArduino] UDP-Sender beendet. {packet_count} Pakete gesendet.")


def client_thread(
    conn: socket.socket,
    addr,
    rows: List[DataRow],
    interval_s: float,
    jitter_ms: int,
    noise_amp: float,
    extended: bool,
    loop: bool,
    http_mode: bool,
    follow_timestamps: bool,
    timestamp_scale: float,
):
    """Legacy TCP client thread für Rückwärtskompatibilität."""
    name = f"{addr[0]}:{addr[1]}"
    print(f"[MockArduino] TCP Client verbunden: {name}")
    try:
        if http_mode:
            # Versuche eine einfache HTTP Request-Zeile zu lesen (nicht strikt nötig)
            try:
                conn.settimeout(0.2)
                _req = conn.recv(1024)
            except OSError:
                _req = b""
            finally:
                try:
                    conn.settimeout(None)
                except OSError:
                    pass

            # Antworte mit Transfer-Encoding: chunked für kontinuierliches Streaming
            header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                "Cache-Control: no-cache, no-store, must-revalidate\r\n"
                "Pragma: no-cache\r\n"
                "Expires: 0\r\n"
                "Transfer-Encoding: chunked\r\n"
                "Connection: close\r\n\r\n"
            )
            conn.sendall(header.encode("utf-8"))

        idx = 0
        n = len(rows)
        while not STOP_EVENT.is_set():
            row = rows[idx]
            noisy = apply_noise(row, noise_amp)
            line = noisy.to_csv_extended() if extended else noisy.to_csv_basic()
            try:
                if http_mode:
                    # Chunked Encoding: <hexlen>\r\n<data>\r\n
                    data = (line + "\n").encode("utf-8")
                    chunk = f"{len(data):X}\r\n".encode("utf-8") + data + b"\r\n"
                    conn.sendall(chunk)
                else:
                    conn.sendall(line.encode("utf-8") + b"\n")
            except BrokenPipeError:
                break

            next_idx = idx + 1
            end_of_cycle = False
            if next_idx >= n:
                if loop:
                    next_idx = 0
                else:
                    end_of_cycle = True

            # Delay Berechnung
            if follow_timestamps and not end_of_cycle:
                # Nutze Differenz der current_time Felder
                raw_delta = rows[next_idx].current_time - row.current_time
                if raw_delta < 0:
                    # Falls Zeit zurückspringt (unerwartet) -> kein Delay
                    delay = 0.0
                else:
                    # timestamp_scale: z.B. 1000.0 wenn Werte in ms vorliegen
                    delay = raw_delta / timestamp_scale
            else:
                delay = interval_s

            if jitter_ms > 0:
                delta = random.uniform(-jitter_ms / 1000.0, jitter_ms / 1000.0)
                delay = max(0.0, delay + delta)
            if delay > 0:
                time.sleep(delay)

            idx = next_idx
            if end_of_cycle:
                if not loop:
                    if http_mode:
                        try:
                            conn.sendall(b"0\r\n\r\n")
                        except OSError:
                            pass
                    break
    finally:
        try:
            conn.close()
        except OSError:
            pass
        print(f"[MockArduino] Client getrennt: {name}")


def run_udp_server(
    host: str,
    port: int,
    rows: List[DataRow],
    rate: float,
    jitter_ms: int,
    noise_amp: float,
    loop: bool,
    follow_timestamps: bool,
    timestamp_scale: float,
    target_host: Optional[str] = None,
    target_port: Optional[int] = None,
):
    """UDP Server - sendet Pakete kontinuierlich oder wartet auf Client-Requests."""
    interval_s = 1.0 / rate if rate > 0 else 0.01
    marker_filename = f"mock_arduino_server_{host}_{port}.marker"
    marker_path = os.path.join(gettempdir(), marker_filename)

    try:
        # Marker-Datei anlegen
        with open(marker_path, "w", encoding="utf-8") as mf:
            mf.write(f"pid={os.getpid()}\nport={port}\nmode=udp\n")
        print(f"[MockArduino] Marker-Datei erstellt: {marker_path}")

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # Für UDP-Server: Binde an alle Interfaces wenn externe IP angegeben,
            # ansonsten an die angegebene lokale Adresse
            bind_host = host
            if not host.startswith("127.") and not host.startswith("0.0.0.0"):
                # Wenn externe IP angegeben, binde an alle Interfaces
                bind_host = "0.0.0.0"
                print(
                    f"[MockArduino] Binde an alle Interfaces (0.0.0.0:{port}) für externe Erreichbarkeit"
                )

            try:
                sock.bind((bind_host, port))
            except OSError as e:
                if bind_host != "0.0.0.0":
                    print(
                        f"[MockArduino] Binding an {bind_host}:{port} fehlgeschlagen, versuche 0.0.0.0:{port}"
                    )
                    bind_host = "0.0.0.0"
                    sock.bind((bind_host, port))
                else:
                    raise e

            sock.settimeout(1.0)

            print(f"[MockArduino] UDP Server gestartet auf {bind_host}:{port}")
            if bind_host != host:
                print(
                    f"[MockArduino] Server erreichbar über alle Interfaces, ursprünglich angefragt: {host}:{port}"
                )
            print(
                f"[MockArduino] Format: UDP (8 Werte) | Rate ~{rate} Pakete/s | Loop={loop}"
            )
            if follow_timestamps:
                print(
                    f"[MockArduino] Timing=CSV current_time Differenzen (Scale={timestamp_scale})"
                )
            print("[MockArduino] Zum Stoppen Ctrl+C drücken ...")

            # Wenn Zieladresse angegeben, starte kontinuierliches Senden
            if target_host and target_port:
                target_addr = (target_host, target_port)
                print(
                    f"[MockArduino] Kontinuierliches Senden an {target_host}:{target_port}"
                )
                udp_sender_thread(
                    sock,
                    target_addr,
                    rows,
                    interval_s,
                    jitter_ms,
                    noise_amp,
                    loop,
                    follow_timestamps,
                    timestamp_scale,
                )
            else:
                # Warte auf eingehende Pakete und antworte
                clients = {}  # Dict um letzte Client-Adressen zu speichern

                while not STOP_EVENT.is_set():
                    try:
                        # Warte auf eingehende Nachricht
                        data, addr = sock.recvfrom(1024)
                        client_key = f"{addr[0]}:{addr[1]}"

                        if client_key not in clients:
                            print(f"[MockArduino] Neuer UDP-Client: {client_key}")
                            clients[client_key] = addr

                            # Starte Sender-Thread für diesen Client
                            sender = threading.Thread(
                                target=udp_sender_thread,
                                args=(
                                    sock,
                                    addr,
                                    rows,
                                    interval_s,
                                    jitter_ms,
                                    noise_amp,
                                    loop,
                                    follow_timestamps,
                                    timestamp_scale,
                                ),
                                daemon=True,
                            )
                            sender.start()

                    except socket.timeout:
                        continue
                    except OSError as e:
                        if not STOP_EVENT.is_set():
                            print(f"[MockArduino] UDP-Fehler: {e}")
                        break

    finally:
        # Marker entfernen
        if os.path.exists(marker_path):
            try:
                os.remove(marker_path)
                print(f"[MockArduino] Marker-Datei entfernt: {marker_path}")
            except OSError:
                print(
                    f"[MockArduino] Marker-Datei konnte nicht gelöscht werden: {marker_path}"
                )
        print("[MockArduino] UDP Server gestoppt")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mock Arduino UDP Daten-Streamer")
    p.add_argument(
        "--port", "-p", type=int, default=8080, help="UDP Port (Default 8080)"
    )
    p.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Bind Host (Default 0.0.0.0 für alle Interfaces, 127.0.0.1 nur lokal)",
    )
    p.add_argument(
        "--rate",
        "-r",
        type=float,
        default=100.0,
        help="Ziel Pakete/Sekunde (Default 100)",
    )
    p.add_argument(
        "--file",
        "-f",
        type=Path,
        default=Path("tests/mock_daten_ext.csv"),
        help="CSV-Datei mit Basisdaten",
    )
    p.add_argument("--jitter", type=int, default=0, help="Zeit-Jitter in ms (+/-)")
    p.add_argument(
        "--noise",
        type=float,
        default=0.0,
        help="Rausch-Amplitude für Float-Spalten (z.B. 0.02)",
    )
    p.add_argument(
        "--no-loop", action="store_true", help="Nach einfachem Durchlauf stoppen"
    )
    p.add_argument(
        "--follow-timestamps",
        action="store_true",
        help=(
            "Aktiviere pacing durch Differenzen der 'Current Time' Spalte (ignoriert --rate)."
        ),
    )
    p.add_argument(
        "--timestamp-scale",
        type=float,
        default=1000.0,
        help=(
            "Divisor zur Umrechnung der Zeitdifferenzen in Sekunden (Default 1000.0 => Werte sind in ms). "
            "Bei Mikrosekunden z.B. 1e6 setzen."
        ),
    )
    p.add_argument(
        "--target-host",
        type=str,
        help="Ziel-Host für kontinuierliches UDP-Senden (optional)",
    )
    p.add_argument(
        "--target-port",
        type=int,
        help="Ziel-Port für kontinuierliches UDP-Senden (optional)",
    )
    # Legacy TCP-Unterstützung
    p.add_argument(
        "--tcp", action="store_true", help="Verwende TCP statt UDP (Legacy-Modus)"
    )
    p.add_argument(
        "--extended",
        action="store_true",
        help="Erweitertes Format (15 Werte) nur für TCP-Modus",
    )
    p.add_argument(
        "--http",
        action="store_true",
        help="Einfacher HTTP (Transfer-Encoding: chunked) nur für TCP-Modus",
    )
    return p.parse_args(argv)


def run_tcp_server(
    host: str,
    port: int,
    rows: List[DataRow],
    rate: float,
    jitter_ms: int,
    noise_amp: float,
    extended: bool,
    loop: bool,
    http_mode: bool,
    follow_timestamps: bool,
    timestamp_scale: float,
):
    """Legacy TCP Server für Rückwärtskompatibilität."""
    interval_s = 1.0 / rate if rate > 0 else 0.01
    marker_filename = f"mock_arduino_server_{host}_{port}.marker"
    marker_path = os.path.join(gettempdir(), marker_filename)
    try:
        # Marker-Datei anlegen (enthält PID und Timestamp)
        with open(marker_path, "w", encoding="utf-8") as mf:
            mf.write(
                f"pid={os.getpid()}\nport={port}\nmode={'http' if http_mode else 'tcp'}\n"
            )
        print(f"[MockArduino] Marker-Datei erstellt: {marker_path}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Für TCP-Server: Binde an alle Interfaces wenn externe IP angegeben
            bind_host = host
            if not host.startswith("127.") and not host.startswith("0.0.0.0"):
                # Wenn externe IP angegeben, binde an alle Interfaces
                bind_host = "0.0.0.0"
                print(
                    f"[MockArduino] Binde an alle Interfaces (0.0.0.0:{port}) für externe Erreichbarkeit"
                )

            try:
                s.bind((bind_host, port))
            except OSError as e:
                if bind_host != "0.0.0.0":
                    print(
                        f"[MockArduino] Binding an {bind_host}:{port} fehlgeschlagen, versuche 0.0.0.0:{port}"
                    )
                    bind_host = "0.0.0.0"
                    s.bind((bind_host, port))
                else:
                    raise e

            s.listen(5)
            s.settimeout(1.0)
            print(f"[MockArduino] TCP Server gestartet auf {bind_host}:{port}")
            if bind_host != host:
                print(
                    f"[MockArduino] Server erreichbar über alle Interfaces, ursprünglich angefragt: {host}:{port}"
                )
            if follow_timestamps:
                print(
                    f"[MockArduino] Format: {'EXTENDED (15 Werte)' if extended else 'BASIC (9 Werte)'} | Timing=CSV current_time Differenzen (Scale={timestamp_scale}) | Loop={loop}"
                )
            else:
                print(
                    f"[MockArduino] Format: {'EXTENDED (15 Werte)' if extended else 'BASIC (9 Werte)'} | Rate ~{rate} Zeilen/s | Loop={loop}"
                )
            if http_mode:
                print("[MockArduino] HTTP-Modus aktiv (chunked streaming)")
            print("[MockArduino] Zum Stoppen Ctrl+C drücken ...")
            while not STOP_EVENT.is_set():
                try:
                    conn, addr = s.accept()
                except socket.timeout:
                    continue
                thr = threading.Thread(
                    target=client_thread,
                    args=(
                        conn,
                        addr,
                        rows,
                        interval_s,
                        jitter_ms,
                        noise_amp,
                        extended,
                        loop,
                        http_mode,
                        follow_timestamps,
                        timestamp_scale,
                    ),
                    daemon=True,
                )
                thr.start()
    finally:
        # Marker entfernen
        if os.path.exists(marker_path):
            try:
                os.remove(marker_path)
                print(f"[MockArduino] Marker-Datei entfernt: {marker_path}")
            except OSError:
                print(
                    f"[MockArduino] Marker-Datei konnte nicht gelöscht werden: {marker_path}"
                )
        print("[MockArduino] TCP Server gestoppt")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        rows = load_data(args.file)
    except (OSError, ValueError) as e:
        print(f"Fehler beim Laden der Daten: {e}", file=sys.stderr)
        return 1

    loop = not args.no_loop

    if args.tcp:
        # Legacy TCP-Modus
        run_tcp_server(
            host=args.host,
            port=args.port,
            rows=rows,
            rate=args.rate,
            jitter_ms=args.jitter,
            noise_amp=args.noise,
            extended=args.extended,
            loop=loop,
            http_mode=args.http,
            follow_timestamps=args.follow_timestamps,
            timestamp_scale=args.timestamp_scale,
        )
    else:
        # Standard UDP-Modus
        run_udp_server(
            host=args.host,
            port=args.port,
            rows=rows,
            rate=args.rate,
            jitter_ms=args.jitter,
            noise_amp=args.noise,
            loop=loop,
            follow_timestamps=args.follow_timestamps,
            timestamp_scale=args.timestamp_scale,
            target_host=args.target_host,
            target_port=args.target_port,
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
