#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock Arduino WiFi Daten-Streamer
================================

Dieses Skript emuliert das Verhalten des Arduino-Sketches `wifi_spi.ino`.
Es startet einen einfachen TCP-Server (kein echtes HTTP), akzeptiert
Client-Verbindungen (z.B. via `nc localhost 8080`) und streamt kontinuierlich
Sensordaten-Zeilen im CSV-Format. Die Daten basieren auf der Datei
`tests/mock_data.csv` und werden in einer Endlosschleife abgespielt.

Standard-Format (entspricht mock_data.csv):
    Current Time, Last Interrupt Time, Second Last Interrupt,
    Acceleration X, Acceleration Y, Acceleration Z,
    Gyro X, Gyro Y, Gyro Z

Der aktuelle Arduino-Code (wifi_spi.ino) sendet 15 Werte (verdoppelte Acc/Gyro).
Optional kann dieses erweiterte Format mit --extended aktiviert werden.

Nutzung:
    python scripts/mock_arduino_server.py --port 8080 --rate 100

Dann verbinden, z.B.:
    nc 127.0.0.1 8080
oder im Browser (es erscheinen nur rohe Zeilen):
    http://127.0.0.1:8080

Argumente:
    --port / -p        TCP-Port (Default 8080)
    --rate / -r        Zeilen pro Sekunde (Default 100 → ca. 10 ms Interval)
    --file / -f        Pfad zu CSV (Default tests/mock_data.csv)
    --jitter           Zufälliges zeitliches Jitter (ms) ± (Default 0)
    --noise            Kleine zufällige Rausch-Amplitude für float-Spalten (Default 0.0)
    --extended         Verdopple Acc/Gyro-Werte wie in wifi_spi.ino (15 Spalten)
    --no-loop          Höre nach einmaligem Durchlauf auf (Standard: Endlosschleife)

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
from dataclasses import dataclass
from tempfile import gettempdir
import os
from pathlib import Path
from typing import List

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
    last_interrupt: int
    second_last_interrupt: int
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float

    def to_csv_basic(self) -> str:
        return f"{self.current_time},{self.last_interrupt},{self.second_last_interrupt},{self.ax:.2f},{self.ay:.2f},{self.az:.2f},{self.gx:.2f},{self.gy:.2f},{self.gz:.2f}"  # noqa: E501

    def to_csv_extended(self) -> str:
        # Repliziert das Muster aus wifi_spi.ino (Acc/Gyro Blöcke dupliziert)
        return (
            f"{self.current_time},{self.last_interrupt},{self.second_last_interrupt},"
            f"{self.ax:.2f},{self.ay:.2f},{self.az:.2f},{self.gx:.2f},{self.gy:.2f},{self.gz:.2f},"
            f"{self.ax:.2f},{self.ay:.2f},{self.az:.2f},{self.gx:.2f},{self.gy:.2f},{self.gz:.2f}"
        )


def load_data(path: Path) -> List[DataRow]:
    if not path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")

    rows: List[DataRow] = []
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
                        rows.append(
                            DataRow(
                                int(values[0]),
                                int(values[1]),
                                int(values[2]),
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
                rows.append(
                    DataRow(
                        int(values[0]),
                        int(values[1]),
                        int(values[2]),
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


def apply_noise(row: DataRow, noise_amp: float) -> DataRow:
    if noise_amp <= 0:
        return row
    # Füge leichtes Rauschen auf die Float-Werte hinzu
    return DataRow(
        current_time=row.current_time,
        last_interrupt=row.last_interrupt,
        second_last_interrupt=row.second_last_interrupt,
        ax=row.ax + random.uniform(-noise_amp, noise_amp),
        ay=row.ay + random.uniform(-noise_amp, noise_amp),
        az=row.az + random.uniform(-noise_amp, noise_amp),
        gx=row.gx + random.uniform(-noise_amp, noise_amp),
        gy=row.gy + random.uniform(-noise_amp, noise_amp),
        gz=row.gz + random.uniform(-noise_amp, noise_amp),
    )


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
):  # noqa: D401
    name = f"{addr[0]}:{addr[1]}"
    print(f"[MockArduino] Client verbunden: {name}")
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

            idx += 1
            if idx >= n:
                if not loop:
                    if http_mode:
                        # Sende abschließenden leeren Chunk, damit Browser sauber schließt
                        try:
                            conn.sendall(b"0\r\n\r\n")
                        except OSError:
                            pass
                    break
                idx = 0

            delay = interval_s
            if jitter_ms > 0:
                delta = random.uniform(-jitter_ms / 1000.0, jitter_ms / 1000.0)
                delay = max(0.0, delay + delta)
            if delay > 0:
                time.sleep(delay)
    finally:
        try:
            conn.close()
        except OSError:
            pass
        print(f"[MockArduino] Client getrennt: {name}")


def run_server(
    host: str,
    port: int,
    rows: List[DataRow],
    rate: float,
    jitter_ms: int,
    noise_amp: float,
    extended: bool,
    loop: bool,
    http_mode: bool,
):
    interval_s = 1.0 / rate if rate > 0 else 0.01
    marker_filename = f"mock_arduino_server_{host}_{port}.marker"
    marker_path = os.path.join(gettempdir(), marker_filename)
    try:
        # Marker-Datei anlegen (enthält PID und Timestamp)
        with open(marker_path, "w", encoding="utf-8") as mf:
            mf.write(
                f"pid={os.getpid()}\nport={port}\nmode={'http' if http_mode else 'raw'}\n"
            )
        print(f"[MockArduino] Marker-Datei erstellt: {marker_path}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.listen(5)
            s.settimeout(1.0)
            print(f"[MockArduino] Server gestartet auf {host}:{port}")
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
        print("[MockArduino] Server gestoppt")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mock Arduino WiFi Daten-Streamer")
    p.add_argument(
        "--port", "-p", type=int, default=8080, help="TCP Port (Default 8080)"
    )
    p.add_argument(
        "--host", type=str, default="127.0.0.1", help="Bind Host (Default 127.0.0.1)"
    )
    p.add_argument(
        "--rate",
        "-r",
        type=float,
        default=100.0,
        help="Ziel Zeilen/Sekunde (Default 100)",
    )
    p.add_argument(
        "--file",
        "-f",
        type=Path,
        default=Path("tests/mock_data.csv"),
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
        "--extended",
        action="store_true",
        help="Erweitertes Format (15 Werte) wie aktueller Sketch",
    )
    p.add_argument(
        "--no-loop", action="store_true", help="Nach einfachem Durchlauf stoppen"
    )
    p.add_argument(
        "--http",
        action="store_true",
        help="Einfacher HTTP (Transfer-Encoding: chunked) für Browser-Zugriff",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        rows = load_data(args.file)
    except (OSError, ValueError) as e:
        print(f"Fehler beim Laden der Daten: {e}", file=sys.stderr)
        return 1
    loop = not args.no_loop
    run_server(
        host=args.host,
        port=args.port,
        rows=rows,
        rate=args.rate,
        jitter_ms=args.jitter,
        noise_amp=args.noise,
        extended=args.extended,
        loop=loop,
        http_mode=args.http,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
