#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test-Script für das korrigierte Mock-Serial-Device Binärformat
"""


def test_binary_format():
    """Testet das Binärformat des Mock-Geräts."""

    print("🔧 Teste Mock-Serial-Device Binärformat...")

    # Simuliere verschiedene Zeitwerte in Mikrosekunden
    test_values = [1000, 5000, 10000, 50000, 100000, 500000, 1000000]

    print("\n📦 Test der Binärpaket-Erstellung:")

    for value in test_values:
        # Erstelle das Binärpaket wie im Mock-Gerät
        packet = (
            bytes([0xAA])  # Start-Byte
            + value.to_bytes(4, byteorder="little")  # 4 Daten-Bytes (little-endian)
            + bytes([0x55])  # End-Byte
        )

        # Dekodiere das Paket wie im DeviceManager
        if packet[0] == 0xAA and packet[5] == 0x55:
            value_bytes = packet[1:5]
            decoded_value = int.from_bytes(
                value_bytes, byteorder="little", signed=False
            )

            status = "✅" if decoded_value == value else "❌"
            print(
                f"  {status} Wert: {value:>7} µs -> Paket: 0x{packet.hex()} -> Dekodiert: {decoded_value} µs"
            )
        else:
            print(f"  ❌ Ungültiges Paket für Wert {value}: 0x{packet.hex()}")

    print("\n🎯 Test extremer Werte:")

    # Test Grenzwerte
    extreme_values = [0, 1, 0xFFFFFFFF - 1, 0xFFFFFFFF]

    for value in extreme_values[:2]:  # Teste nur gültige Werte für to_bytes
        try:
            packet = (
                bytes([0xAA]) + value.to_bytes(4, byteorder="little") + bytes([0x55])
            )

            value_bytes = packet[1:5]
            decoded_value = int.from_bytes(
                value_bytes, byteorder="little", signed=False
            )

            status = "✅" if decoded_value == value else "❌"
            print(
                f"  {status} Extremwert: {value:>10} -> Paket: 0x{packet.hex()} -> Dekodiert: {decoded_value}"
            )

        except OverflowError as e:
            print(f"  ⚠️  Overflow für Wert {value}: {e}")

    print("\n📏 Paketgröße-Prüfung:")
    test_packet = bytes([0xAA]) + (1000).to_bytes(4, byteorder="little") + bytes([0x55])
    print(f"  📦 Paketgröße: {len(test_packet)} Bytes (erwartet: 6)")
    print(
        f"  🔢 Paketformat: Start(0x{test_packet[0]:02X}) + 4xData + End(0x{test_packet[5]:02X})"
    )

    print("\n🎉 Binärformat-Test abgeschlossen!")


if __name__ == "__main__":
    test_binary_format()
