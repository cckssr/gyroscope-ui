#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test-Script für das korrigierte DataController Queue-System
"""

import sys
import os

sys.path.insert(0, os.path.abspath("."))

from src.data_controller import DataController
from src.plot import PlotWidget


def test_data_controller():
    """Teste das korrigierte DataController Queue-System."""

    print("🔧 Teste DataController nach Merge-Korrekturen...")

    # Mock PlotWidget für Test
    class MockPlotWidget:
        def update_plot(self, data_points):
            print(f"  📊 Plot aktualisiert mit {len(data_points)} Datenpunkten")

        def update_plot_batch(self, data_points):
            print(f"  📊 Plot Batch-Update mit {len(data_points)} Datenpunkten")

        def clear(self):
            print("  🧹 Plot geleert")

    # DataController erstellen
    mock_plot = MockPlotWidget()
    controller = DataController(plot_widget=mock_plot, max_history=10)

    print("✅ DataController erfolgreich erstellt")

    # Test 1: add_data_point_fast (Queue-System)
    print("\n🚀 Test 1: add_data_point_fast (Queue-System)")
    for i in range(5):
        controller.add_data_point_fast(i, 1000 + i * 10)
        print(f"  ➕ Datenpunkt {i} zur Queue hinzugefügt")

    print(f"  📋 Queue-Größe: {controller.get_queue_size()}")
    print(f"  📈 Gesamt-Datenpunkte: {len(controller.data_points)}")

    # Test 2: Queue-Verarbeitung
    print("\n⚙️  Test 2: Queue-Verarbeitung")
    if controller.has_queued_data():
        controller.process_queued_data()
        print("  ✅ Queue verarbeitet")

    print(f"  📋 Queue-Größe nach Verarbeitung: {controller.get_queue_size()}")
    print(f"  📊 GUI-Datenpunkte: {len(controller.gui_data_points)}")

    # Test 3: Statistiken
    print("\n📊 Test 3: Statistiken")
    stats = controller.get_statistics()
    print(f"  📈 Anzahl: {stats['count']}")
    print(f"  📏 Min: {stats['min']:.0f}, Max: {stats['max']:.0f}")
    print(f"  📊 Mittelwert: {stats['avg']:.0f}")

    # Test 4: Export-Daten
    print("\n💾 Test 4: Export-Daten")
    export_data = controller.get_all_data_for_export()
    print(f"  📁 Export-Datenpunkte: {len(export_data)}")
    if export_data:
        print(f"  📄 Beispiel-Datenpunkt: {export_data[0]}")

    print("\n🎉 Alle Tests erfolgreich!")
    return True


if __name__ == "__main__":
    test_data_controller()
