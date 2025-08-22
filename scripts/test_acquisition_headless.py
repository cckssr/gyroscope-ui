#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Headless-Test für die CSV Acquisition (ohne MainWindow / Plot).

Startet einen minimalen Qt-Eventloop (QCoreApplication), verbindet sich per
``DeviceManager`` mit dem Mock-Server (oder realem Gerät) und sammelt eine
konfigurierbare Anzahl Datenpunkte. Danach werden einfache Statistiken für die
Multi-Messwerte (Frequenz, Accel Z, Gyro Z) ausgegeben.

Beispiel:
    1) Mock Server starten (in zweitem Terminal):
        python scripts/mock_arduino_server.py -p 8080 -r 200

    2) Headless Acquisition Test:
        python scripts/test_acquisition_headless.py --ip 127.0.0.1:8080 --points 1000

Optional kann eine Dauer statt einer Punktanzahl genutzt werden:
        python scripts/test_acquisition_headless.py --ip 127.0.0.1:8080 --seconds 5

Ein CSV Export der empfangenen Multi-Daten ist ebenfalls möglich:
        python scripts/test_acquisition_headless.py --ip 127.0.0.1:8080 -n 500 -o out.csv
"""
from __future__ import annotations

import argparse
import math
import sys
import time
import signal
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

from PySide6.QtCore import QObject, Slot, QTimer, QCoreApplication  # type: ignore

try:
    from src.device_manager import DeviceManager  # type: ignore
    from src.debug_utils import Debug  # type: ignore
except ModuleNotFoundError:
    # Falls Paket nicht installiert ist: Projektwurzel zum sys.path hinzufügen
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.device_manager import DeviceManager  # type: ignore  # noqa: E402
    from src.debug_utils import Debug  # type: ignore  # noqa: E402


@dataclass
class MultiPoint:
    index: int
    frequency: float  # Hz oder NaN
    accel_z: float  # oder NaN
    gyro_z: float  # oder NaN


class AcquisitionCollector(QObject):
    """Sammelt Datenpunkte aus den Signalen des Acquisition-Threads."""

    def __init__(self, max_points: Optional[int], seconds: Optional[float]):
        super().__init__()
        self.max_points = max_points
        self.seconds = seconds
        self.start_time = time.time()
        self.multi_points: List[MultiPoint] = []
        self.single_points = 0  # nur Anzahl für legacy data_point
        self.done = False

    @Slot(int, float)
    def on_single(self, index: int, value: float):  # noqa: D401
        self.single_points += 1

    @Slot(int, float, float, float)
    def on_multi(self, index: int, freq: float, az: float, gz: float):  # noqa: D401
        self.multi_points.append(MultiPoint(index, freq, az, gz))
        # Progress alle 200 Punkte
        if len(self.multi_points) % 200 == 0:
            print(f"[Collector] Punkte: {len(self.multi_points)} (index={index})")
        if self.max_points is not None and len(self.multi_points) >= self.max_points:
            self.done = True

    def time_exceeded(self) -> bool:
        if self.seconds is None:
            return False
        return (time.time() - self.start_time) >= self.seconds

    def should_stop(self) -> bool:
        return self.done or self.time_exceeded()

    def stats(self):  # noqa: D401
        if not self.multi_points:
            return {}

        def col(values):
            vals = [v for v in values if not math.isnan(v)]
            if not vals:
                return {"count": 0}
            return {
                "count": len(vals),
                "min": min(vals),
                "max": max(vals),
                "avg": sum(vals) / len(vals),
            }

        freq_stats = col([p.frequency for p in self.multi_points])
        az_stats = col([p.accel_z for p in self.multi_points])
        gz_stats = col([p.gyro_z for p in self.multi_points])
        return {"frequency": freq_stats, "accel_z": az_stats, "gyro_z": gz_stats}

    def to_csv(self) -> str:
        lines = ["index,frequency,accel_z,gyro_z"]
        for p in self.multi_points:

            def f(x: float) -> str:
                return "" if math.isnan(x) else f"{x:.6f}"

            lines.append(f"{p.index},{f(p.frequency)},{f(p.accel_z)},{f(p.gyro_z)}")
        return "\n".join(lines) + "\n"


def parse_args(argv: List[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Headless Acquisition Test")
    ap.add_argument("--ip", required=True, help="Ziel IP:Port (z.B. 127.0.0.1:8080)")
    ap.add_argument(
        "-n", "--points", type=int, default=None, help="Anzahl Punkte sammeln"
    )
    ap.add_argument(
        "-s",
        "--seconds",
        type=float,
        default=None,
        help="Alternative: Sekunden sammeln",
    )
    ap.add_argument(
        "-o", "--output", type=str, default=None, help="CSV-Datei für Multi-Daten"
    )
    ap.add_argument(
        "--primary",
        type=str,
        default="accel_magnitude",
        help="Primärfeld für legacy value",
    )
    ap.add_argument("--verbose", action="store_true", help="Verbose Debug aktivieren")
    return ap.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    # Debug initialisieren
    Debug.init(
        debug_level=Debug.DEBUG_VERBOSE if args.verbose else Debug.DEBUG_OFF,
        app_name="HeadlessTest",
    )

    if args.points is None and args.seconds is None:
        print("Bitte entweder --points oder --seconds angeben", file=sys.stderr)
        return 2

    app = QCoreApplication([])

    manager = DeviceManager()
    manager.set_primary_field(args.primary)

    if not manager.connect(args.ip, timeout=2.0):
        print(f"Verbindung zu {args.ip} fehlgeschlagen", file=sys.stderr)
        return 1

    collector = AcquisitionCollector(max_points=args.points, seconds=args.seconds)

    # Signale verbinden
    # Thread wird beim start_acquisition erzeugt – erst danach verbinden, falls interner Thread später neu gestartet wird
    def ensure_connections():
        if manager.acquire_thread:
            # Nur verbinden, wenn noch nicht verbunden
            try:
                manager.acquire_thread.data_point.connect(collector.on_single)
            except Exception:
                pass
            try:
                manager.acquire_thread.multi_data_point.connect(collector.on_multi)
            except Exception:
                pass

    manager.start_acquisition()
    ensure_connections()

    print("[Headless] Acquisition gestartet … (Ctrl+C zum Abbrechen)")

    # --- SIGINT Handling (Ctrl+C) ---
    stop_flag = {"requested": False}

    def _sigint_handler(_signum, _frame):  # noqa: D401
        if stop_flag["requested"]:
            # Zweites Ctrl+C erzwingt sofortigen Abbruch
            print("[Headless] Force Exit")
            os._exit(130)  # noqa: PLR1722
        print("\n[Headless] Ctrl+C erkannt – Stop wird eingeleitet …")
        stop_flag["requested"] = True

    try:
        signal.signal(signal.SIGINT, _sigint_handler)
    except Exception:
        pass  # Auf manchen Plattformen evtl. nicht verfügbar

    # Periodischer Check ob wir stoppen sollen
    def poll_stop():  # noqa: D401
        if stop_flag["requested"] and not collector.done:
            # Benutzerabbruch -> sofortiges Stop-Kriterium setzen
            collector.done = True
        if collector.should_stop():
            print("[Headless] Stop-Kriterium erreicht – fahre herunter …")
            stats = collector.stats()
            print("\n=== Statistiken ===")
            for name, st in stats.items():
                if not st:
                    continue
                if st.get("count", 0) == 0:
                    print(f"{name}: keine Werte")
                else:
                    print(
                        f"{name}: count={st['count']} min={st['min']:.3f} max={st['max']:.3f} avg={st['avg']:.3f}"
                    )
            if args.output:
                try:
                    with open(args.output, "w", encoding="utf-8") as f:
                        f.write(collector.to_csv())
                    print(f"CSV geschrieben: {args.output}")
                except OSError as e:
                    print(f"Fehler beim Schreiben {args.output}: {e}")
            manager.shutdown()
            app.quit()

    timer = QTimer()
    timer.timeout.connect(poll_stop)
    timer.start(200)

    # Fallback Stop (Sicherheitsnetz) nach 10 Minuten
    def hard_timeout():  # noqa: D401
        print("[Headless] Hard Timeout – Abbruch")
        manager.shutdown()
        app.quit()

    hard_timer = QTimer()
    hard_timer.setSingleShot(True)
    hard_timer.timeout.connect(hard_timeout)
    hard_timer.start(10 * 60 * 1000)

    try:
        exit_code = app.exec()
    except KeyboardInterrupt:
        print("\n[Headless] KeyboardInterrupt – Shutdown …")
        try:
            manager.shutdown()
        except Exception:
            pass
        exit_code = 130
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
