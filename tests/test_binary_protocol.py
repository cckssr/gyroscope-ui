#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test-Skript für das binäre Protokoll: 0xAA + 4 Bytes."""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def test_binary_protocol():
    """Teste die binäre Paket-Verarbeitung."""
    print("=== Test des binären Protokolls (0xAA + 4 Bytes) ===")

    # Teste verschiedene Werte
    test_values = [
        0x00000000,  # Minimum
        0x000003E8,  # 1000
        0x0000FFFF,  # 65535
        0xFFFFFFFF,  # Maximum (4294967295)
        0x12345678,  # Test-Pattern
    ]

    START_BYTE = 0xAA

    for value in test_values:
        # Erstelle binäres Paket
        value_bytes = value.to_bytes(4, byteorder="little", signed=False)
        packet = bytes([START_BYTE]) + value_bytes

        print(f"\nTest-Wert: {value} (0x{value:08X})")
        print(f"Binäres Paket: 0x{packet.hex().upper()}")
        print(f"Bytes: {[hex(b) for b in packet]}")

        # Simuliere Dekodierung
        if packet[0] == START_BYTE and len(packet) == 5:
            decoded_value = int.from_bytes(
                packet[1:5], byteorder="little", signed=False
            )
            print(f"Dekodiert: {decoded_value}")
            print(f"Korrekt: {'✓' if decoded_value == value else '✗'}")
        else:
            print("Fehler: Ungültiges Paket")

    print("\n=== Test mit gestörten Daten ===")

    # Test mit gestörten Daten
    test_data = bytearray(
        [
            0x11,
            0x22,
            0x33,  # Müll am Anfang
            0xAA,
            0x01,
            0x00,
            0x00,
            0x00,  # Gültiges Paket (Wert: 1)
            0x44,
            0x55,  # Müll dazwischen
            0xAA,
            0xE8,
            0x03,
            0x00,
            0x00,  # Gültiges Paket (Wert: 1000)
            0x66,  # Unvollständiges Paket
            0xAA,
            0xFF,
            0xFF,  # Unvollständiges Paket
        ]
    )

    print(f"Test-Daten: 0x{test_data.hex().upper()}")

    # Simuliere Paket-Extraktion
    buffer = bytes(test_data)
    packets_found = []

    i = 0
    while i < len(buffer):
        if buffer[i] == START_BYTE and i + 4 < len(buffer):
            packet = buffer[i : i + 5]
            value = int.from_bytes(packet[1:5], byteorder="little", signed=False)
            packets_found.append(value)
            print(
                f"Gefundenes Paket bei Position {i}: 0x{packet.hex().upper()} -> Wert: {value}"
            )
            i += 5
        else:
            i += 1

    expected_values = [1, 1000]
    print(f"\nErwartete Werte: {expected_values}")
    print(f"Gefundene Werte: {packets_found}")
    print(
        f"Test: {'✓ ERFOLGREICH' if packets_found == expected_values else '✗ FEHLGESCHLAGEN'}"
    )


if __name__ == "__main__":
    test_binary_protocol()
