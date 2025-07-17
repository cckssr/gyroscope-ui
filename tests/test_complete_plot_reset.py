#!/usr/bin/env python3
"""Integrationstest für Plot-Reset bei neuer Messung."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.data_controller import DataController
from src.device_manager import DataAcquisitionThread
from unittest.mock import Mock


def test_complete_plot_reset():
    """Test des kompletten Plot-Reset-Workflows."""

    print("=== Integrationstest: Kompletter Plot-Reset bei neuer Messung ===")

    # Mock PlotWidget
    class MockPlotWidget:
        def __init__(self):
            self.cleared = False
            self.points = []

        def update_plot_batch(self, points):
            self.points.extend(points)

        def clear(self):
            self.cleared = True
            self.points = []
            print("PlotWidget.clear() aufgerufen")

    plot_widget = MockPlotWidget()

    # DataController mit sehr kleinem history_limit
    controller = DataController(plot_widget=plot_widget, max_history=5)

    print("1. Erste Messung: Füge 8 Datenpunkte hinzu...")
    for i in range(8):
        controller.add_data_point(i, float(i * 10))

    full_data_1 = controller.get_all_data_for_export()
    data_info_1 = controller.get_data_info()

    print(f"   Vollständige Daten: {len(full_data_1)} Punkte")
    print(f"   GUI-Daten: {data_info_1['gui_data_points']} Punkte")
    print(f"   Plot-Punkte: {len(plot_widget.points)} Punkte")

    # Verifiziere erste Messung
    assert len(full_data_1) == 8, f"Vollständige Daten sollten 8 Punkte haben"
    assert (
        data_info_1["gui_data_points"] == 5
    ), f"GUI-Daten sollten 5 Punkte haben (limit)"

    print("\n2. Neue Messung starten: clear_data() aufrufen...")
    controller.clear_data()

    # Verifiziere Reset
    full_data_2 = controller.get_all_data_for_export()
    data_info_2 = controller.get_data_info()

    print(f"   Plot wurde geleert: {plot_widget.cleared}")
    print(f"   Vollständige Daten nach Reset: {len(full_data_2)} Punkte")
    print(f"   GUI-Daten nach Reset: {data_info_2['gui_data_points']} Punkte")
    print(f"   Plot-Punkte nach Reset: {len(plot_widget.points)} Punkte")

    # Verifiziere Reset
    assert plot_widget.cleared == True, "Plot sollte geleert worden sein"
    assert len(full_data_2) == 0, "Vollständige Daten sollten geleert sein"
    assert data_info_2["gui_data_points"] == 0, "GUI-Daten sollten geleert sein"
    assert len(plot_widget.points) == 0, "Plot-Punkte sollten geleert sein"

    print("\n3. Neue Messung: Füge 3 neue Datenpunkte hinzu...")
    plot_widget.cleared = False  # Reset flag

    for i in range(3):
        controller.add_data_point(i, float(i * 20))  # Andere Werte

    full_data_3 = controller.get_all_data_for_export()
    data_info_3 = controller.get_data_info()

    print(f"   Vollständige Daten: {len(full_data_3)} Punkte")
    print(f"   GUI-Daten: {data_info_3['gui_data_points']} Punkte")
    print(f"   Plot-Punkte: {len(plot_widget.points)} Punkte")
    print(f"   Erste Punkte: {full_data_3[:3] if full_data_3 else 'keine'}")

    # Verifiziere neue Messung startet bei Index 0
    assert len(full_data_3) == 3, "Neue Messung sollte 3 Punkte haben"
    assert data_info_3["gui_data_points"] == 3, "GUI sollte 3 Punkte haben"
    assert (
        full_data_3[0][0] == 0
    ), f"Erster Index sollte 0 sein, ist {full_data_3[0][0]}"
    assert (
        full_data_3[1][0] == 1
    ), f"Zweiter Index sollte 1 sein, ist {full_data_3[1][0]}"
    assert (
        full_data_3[2][0] == 2
    ), f"Dritter Index sollte 2 sein, ist {full_data_3[2][0]}"

    print("\n✅ Alle Tests erfolgreich:")
    print("   ✅ Plot wird korrekt geleert")
    print("   ✅ Vollständige Daten werden zurückgesetzt")
    print("   ✅ GUI-Daten werden zurückgesetzt")
    print("   ✅ Neue Messung startet bei Index 0")
    print("   ✅ Export funktioniert für neue Messung")

    print("\n=== Integrationstest erfolgreich! ===")
    return True


if __name__ == "__main__":
    test_complete_plot_reset()
