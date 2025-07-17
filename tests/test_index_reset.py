#!/usr/bin/env python3
"""Test um zu verifizieren, dass der Plot-Index bei einer neuen Messung zurückgesetzt wird."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.device_manager import DataAcquisitionThread, DeviceManager
from unittest.mock import Mock


def test_index_reset():
    """Test der Index-Reset-Funktionalität."""

    print("=== Test: Index-Reset bei neuer Messung ===")

    # Mock DeviceManager
    mock_manager = Mock()
    mock_manager.device = Mock()
    mock_manager.connected = True
    mock_manager.measurement_active = True

    # DataAcquisitionThread erstellen
    thread = DataAcquisitionThread(mock_manager)

    # Simuliere Datenpunkte durch direktes Setzen des Index
    thread._index = 5  # Simuliere dass bereits 5 Datenpunkte verarbeitet wurden
    print(f"Index vor Reset: {thread._index}")

    # Index zurücksetzen (wie bei neuer Messung)
    thread.reset_index()
    print(f"Index nach Reset: {thread._index}")

    # Verifiziere dass der Index korrekt zurückgesetzt wurde
    assert thread._index == 0, f"Index sollte 0 sein, ist aber {thread._index}"

    print("✅ Index wurde korrekt auf 0 zurückgesetzt")

    # Teste DeviceManager start_measurement mit Mock
    device_manager = DeviceManager()
    device_manager.device = Mock()
    device_manager.connected = True
    device_manager.acquire_thread = thread

    # Setze Index wieder auf einen Wert > 0
    thread._index = 10
    print(f"Index vor start_measurement: {thread._index}")

    # Start measurement sollte Index zurücksetzen
    result = device_manager.start_measurement()
    print(f"Index nach start_measurement: {thread._index}")

    assert result == True, "start_measurement sollte True zurückgeben"
    assert (
        thread._index == 0
    ), f"Index sollte nach start_measurement 0 sein, ist aber {thread._index}"

    print("✅ start_measurement setzt Index korrekt zurück")
    print("=== Test erfolgreich: Index-Reset funktioniert! ===")

    return True


if __name__ == "__main__":
    test_index_reset()
