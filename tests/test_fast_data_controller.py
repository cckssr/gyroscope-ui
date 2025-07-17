#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test-Skript für die neue Fast-Data-Queue-Funktionalität."""

import sys
import time
import threading
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data_controller import DataController
from src.plot import PlotWidget
from src.debug_utils import Debug


def test_fast_data_processing():
    """Teste die schnelle Datenverarbeitung mit Queue."""
    print("=== Test der Fast-Data-Queue-Funktionalität ===")

    # Mock Plot Widget für Test
    class MockPlotWidget:
        def __init__(self):
            self.points = []

        def update_plot(self, point):
            self.points.append(point)

        def clear(self):
            self.points = []

    # DataController erstellen
    plot_widget = MockPlotWidget()
    controller = DataController(plot_widget=plot_widget, gui_update_interval=100)

    print(f"DataController erstellt mit GUI-Update-Intervall: 100ms")

    # Simuliere hochfrequente Datenerfassung
    def generate_fast_data():
        """Simuliert schnelle Datenerzeugung."""
        for i in range(100):
            value = 1000 + i * 10  # Simuliere Mikrosekunden-Werte
            controller.add_data_point_fast(i, value)
            time.sleep(0.01)  # 10ms zwischen Datenpunkten (100 Hz)

    print("Starte schnelle Datenerzeugung (100 Punkte mit 100 Hz)...")

    # Starte Datenerzeugung in separatem Thread
    data_thread = threading.Thread(target=generate_fast_data)
    data_thread.start()

    # Warte auf Fertigstellung
    data_thread.join()

    # Kurz warten, damit Queue verarbeitet wird
    time.sleep(0.2)

    # Performance-Statistiken abrufen
    perf_stats = controller.get_performance_stats()
    print(f"\n=== Performance-Statistiken ===")
    print(f"Gesamte empfangene Punkte: {perf_stats['total_points_received']}")
    print(f"Punkte im letzten Update: {perf_stats['points_in_last_update']}")
    print(f"Queue-Größe: {perf_stats['queue_size']}")
    print(f"Gespeicherte Punkte: {perf_stats['stored_points']}")

    # Normale Statistiken
    stats = controller.get_statistics()
    print(f"\n=== Daten-Statistiken ===")
    print(f"Anzahl Datenpunkte: {int(stats['count'])}")
    print(f"Min: {stats['min']:.1f} µs")
    print(f"Max: {stats['max']:.1f} µs")
    print(f"Mittelwert: {stats['avg']:.1f} µs")
    if stats["count"] > 1:
        print(f"Standardabweichung: {stats['stdev']:.1f} µs")

    # Plot-Updates prüfen
    print(f"\nPlot erhielt {len(plot_widget.points)} Updates")

    # Aufräumen
    controller.stop_gui_updates()
    print("\n=== Test abgeschlossen ===")

    return perf_stats["total_points_received"] > 0 and stats["count"] > 0


if __name__ == "__main__":
    success = test_fast_data_processing()
    print(f"\nTest-Ergebnis: {'ERFOLGREICH' if success else 'FEHLGESCHLAGEN'}")
    sys.exit(0 if success else 1)
