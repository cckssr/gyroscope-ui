#!/usr/bin/env python3
"""Test um zu verifizieren, dass data_points unbegrenzt sind und gui_data_points limitiert."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.data_controller import DataController
from src.plot import PlotWidget


def test_data_separation():
    """Test der Datentrennung zwischen vollständigen und GUI-limitierten Daten."""

    # Mock PlotWidget für den Test
    class MockPlotWidget:
        def update_plot_batch(self, points):
            pass

        def clear(self):
            pass

    # DataController mit sehr kleinem history_limit für den Test
    controller = DataController(
        plot_widget=MockPlotWidget(), max_history=3  # Sehr klein für den Test
    )

    print(
        "=== Test: Datentrennung zwischen vollständigen und GUI-limitierten Daten ==="
    )

    # Füge 10 Datenpunkte hinzu (mehr als das GUI-Limit von 3)
    for i in range(10):
        controller.add_data_point(i, float(i * 10))

    # Teste die Datentrennung
    full_data = controller.get_all_data_for_export()
    data_info = controller.get_data_info()
    csv_data = controller.get_csv_data()

    print(f"Vollständige Datenpunkte (für Export): {len(full_data)}")
    print(f"GUI-Datenpunkte (für Anzeige): {data_info['gui_data_points']}")
    print(f"Max History Limit: {data_info['max_history_limit']}")
    print(f"CSV-Datenzeilen (Header + Daten): {len(csv_data)}")

    # Bestätige die erwarteten Ergebnisse
    assert (
        len(full_data) == 10
    ), f"Vollständige Daten sollten 10 Punkte haben, hat {len(full_data)}"
    assert (
        data_info["gui_data_points"] == 3
    ), f"GUI-Daten sollten 3 Punkte haben (limit), hat {data_info['gui_data_points']}"
    assert (
        len(csv_data) == 11
    ), f"CSV sollte 11 Zeilen haben (Header + 10 Daten), hat {len(csv_data)}"

    print("✅ Alle Datenpunkte werden für Export gespeichert")
    print("✅ GUI-Daten sind korrekt auf max_history limitiert")
    print("✅ CSV-Export enthält ALLE Daten, nicht nur GUI-limitierte")

    # Zeige die Inhalte zur Verifizierung
    print("\nVollständige Exportdaten:")
    for i, (idx, val) in enumerate(full_data):
        print(f"  {i+1}: Index={idx}, Value={val}")

    print(f"\nGUI-limitierte Daten (nur die letzten {data_info['max_history_limit']}):")
    gui_data = data_info["gui_points_for_display"]
    for i, (idx, val) in enumerate(gui_data):
        print(f"  {i+1}: Index={idx}, Value={val}")

    print("\n=== Test erfolgreich: Datentrennung funktioniert korrekt! ===")

    return True


if __name__ == "__main__":
    test_data_separation()
