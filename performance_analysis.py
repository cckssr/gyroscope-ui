#!/usr/bin/env python3
"""
Performance-Analyse-Tool für die Datenakquisition.
Misst die maximale Datenrate und identifiziert Engpässe.
"""

import sys
import os
import time
import threading
from queue import Queue

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.data_controller import DataController
from unittest.mock import Mock


def performance_test_data_controller():
    """Teste die Performance des DataControllers."""

    print("=== Performance-Test: DataController ===")

    # Mock PlotWidget
    class HighPerformancePlotWidget:
        def __init__(self):
            self.update_count = 0
            self.last_update_time = time.time()

        def update_plot_batch(self, points):
            self.update_count += 1

        def clear(self):
            pass

    plot_widget = HighPerformancePlotWidget()

    # DataController mit optimalen Einstellungen
    controller = DataController(
        plot_widget=plot_widget,
        max_history=1000,  # Größerer Puffer
        gui_update_interval=100,  # 100ms GUI-Updates
    )

    # Test verschiedene Datenraten
    test_rates = [100, 500, 1000, 2000, 5000, 10000]  # Hz

    for target_rate in test_rates:
        print(f"\n--- Test: {target_rate} Hz ---")

        # Reset
        controller.clear_data()
        plot_widget.update_count = 0

        # Berechne Interval
        interval = 1.0 / target_rate if target_rate > 0 else 0.001

        # Sende Daten für 2 Sekunden
        start_time = time.time()
        test_duration = 2.0
        sent_points = 0

        while time.time() - start_time < test_duration:
            controller.add_data_point_fast(sent_points, float(sent_points * 10))
            sent_points += 1
            time.sleep(interval)

        end_time = time.time()
        actual_duration = end_time - start_time

        # Warte kurz auf Verarbeitung
        time.sleep(0.5)

        # Hole Performance-Stats
        perf_stats = controller.get_performance_stats()
        data_info = controller.get_data_info()

        actual_rate = sent_points / actual_duration
        processed_rate = perf_stats["total_points_received"] / actual_duration

        print(f"  Ziel-Rate: {target_rate:,} Hz")
        print(
            f"  Gesendete Rate: {actual_rate:.1f} Hz ({sent_points} Punkte in {actual_duration:.2f}s)"
        )
        print(
            f"  Verarbeitete Rate: {processed_rate:.1f} Hz ({perf_stats['total_points_received']} Punkte)"
        )
        print(f"  Queue-Größe: {perf_stats['queue_size']}")
        print(f"  Gespeicherte Punkte: {data_info['total_data_points']}")
        print(f"  GUI-Updates: {plot_widget.update_count}")

        # Erfolgs-Kriterien
        data_loss = (
            (sent_points - perf_stats["total_points_received"]) / sent_points * 100
        )
        if data_loss < 1:  # < 1% Datenverlust
            print(f"  ✅ SUCCESS: {data_loss:.2f}% Datenverlust")
        else:
            print(f"  ❌ FAIL: {data_loss:.2f}% Datenverlust")

        if perf_stats["queue_size"] > 1000:
            print(f"  ⚠️  WARNING: Queue-Overflow ({perf_stats['queue_size']} Elemente)")


def performance_test_serial_simulation():
    """Simuliere seriellen Datenverkehr mit verschiedenen Raten."""

    print("\n=== Performance-Test: Serielle Daten-Simulation ===")

    def simulate_packet_processing(packet_rate_hz, test_duration=2.0):
        """Simuliere die Verarbeitung von binären Paketen."""

        # Simuliere das 6-Byte-Protokoll
        START_BYTE = 0xAA
        END_BYTE = 0x55
        PACKET_SIZE = 6

        packets_processed = 0
        byte_buffer = b""

        start_time = time.time()
        packet_interval = 1.0 / packet_rate_hz
        next_packet_time = start_time

        while time.time() - start_time < test_duration:
            current_time = time.time()

            # Erzeuge neues Paket wenn Zeit erreicht
            if current_time >= next_packet_time:
                # Erzeuge 6-Byte-Paket
                value = packets_processed
                value_bytes = value.to_bytes(4, byteorder="little", signed=False)
                packet = bytes([START_BYTE]) + value_bytes + bytes([END_BYTE])

                # Füge zum Buffer hinzu
                byte_buffer += packet
                next_packet_time += packet_interval

            # Verarbeite alle vollständigen Pakete im Buffer
            while len(byte_buffer) >= PACKET_SIZE:
                # Extrahiere Paket
                packet = byte_buffer[:PACKET_SIZE]
                byte_buffer = byte_buffer[PACKET_SIZE:]

                # Validiere und verarbeite
                if packet[0] == START_BYTE and packet[5] == END_BYTE:
                    value_bytes = packet[1:5]
                    value = int.from_bytes(
                        value_bytes, byteorder="little", signed=False
                    )
                    packets_processed += 1

                    # Simuliere emit (minimaler Overhead)
                    pass
                else:
                    # Ungültiges Paket - in echter Implementation würde hier Resynchronisation stattfinden
                    pass

            # Simuliere kleine Pause wie im echten Code
            time.sleep(0.0005)  # 0.5ms wie im Original

        actual_duration = time.time() - start_time
        actual_rate = packets_processed / actual_duration

        return packets_processed, actual_rate, actual_duration

    # Teste verschiedene Paket-Raten
    test_rates = [100, 500, 1000, 2000, 5000, 10000, 20000]

    for target_rate in test_rates:
        packets, actual_rate, duration = simulate_packet_processing(target_rate, 2.0)
        data_loss = (target_rate * duration - packets) / (target_rate * duration) * 100

        print(
            f"  {target_rate:>5} Hz -> {actual_rate:>7.1f} Hz ({packets:>5} Pakete, {data_loss:>5.1f}% Loss)"
        )

        if actual_rate < target_rate * 0.95:  # < 95% der Zielrate
            print(f"    ❌ Performance-Problem bei {target_rate} Hz")
            break
        elif data_loss > 5:  # > 5% Datenverlust
            print(f"    ⚠️  Hoher Datenverlust bei {target_rate} Hz")


def identify_bottlenecks():
    """Identifiziere spezifische Performance-Engpässe."""

    print("\n=== Bottleneck-Analyse ===")

    # 1. Queue-Operations-Test
    print("1. Queue-Performance:")
    q = Queue()

    start_time = time.time()
    for i in range(100000):
        q.put((i, float(i)))
    end_time = time.time()

    queue_put_rate = 100000 / (end_time - start_time)
    print(f"   Queue put(): {queue_put_rate:,.0f} ops/sec")

    start_time = time.time()
    while not q.empty():
        q.get_nowait()
    end_time = time.time()

    queue_get_rate = 100000 / (end_time - start_time)
    print(f"   Queue get(): {queue_get_rate:,.0f} ops/sec")

    # 2. Signal/Slot-Performance (simuliert)
    print("\n2. Signal/Slot-Overhead:")

    class MockSignal:
        def __init__(self):
            self.callbacks = []

        def connect(self, callback):
            self.callbacks.append(callback)

        def emit(self, *args):
            for callback in self.callbacks:
                callback(*args)

    signal = MockSignal()
    received_count = 0

    def receiver(index, value):
        nonlocal received_count
        received_count += 1

    signal.connect(receiver)

    start_time = time.time()
    for i in range(10000):
        signal.emit(i, float(i))
    end_time = time.time()

    signal_rate = 10000 / (end_time - start_time)
    print(f"   Signal emit(): {signal_rate:,.0f} ops/sec")

    # 3. Byte-Processing-Performance
    print("\n3. Byte-Verarbeitung:")

    test_data = b"\xaa\x01\x02\x03\x04\x55" * 10000

    start_time = time.time()
    processed = 0
    i = 0
    while i < len(test_data) - 5:
        if test_data[i] == 0xAA and test_data[i + 5] == 0x55:
            value_bytes = test_data[i + 1 : i + 5]
            value = int.from_bytes(value_bytes, byteorder="little", signed=False)
            processed += 1
            i += 6
        else:
            i += 1
    end_time = time.time()

    byte_processing_rate = processed / (end_time - start_time)
    print(f"   Byte-Verarbeitung: {byte_processing_rate:,.0f} packets/sec")

    print(f"\n=== Empfohlene maximale Datenrate ===")
    print(
        f"   Basierend auf Queue-Performance: {min(queue_put_rate, queue_get_rate) / 10:,.0f} Hz"
    )
    print(f"   Basierend auf Signal-Performance: {signal_rate / 10:,.0f} Hz")
    print(f"   Basierend auf Byte-Processing: {byte_processing_rate / 10:,.0f} Hz")

    max_safe_rate = (
        min(queue_put_rate, queue_get_rate, signal_rate, byte_processing_rate) / 20
    )
    print(f"   Empfohlene sichere Rate: {max_safe_rate:,.0f} Hz")


if __name__ == "__main__":
    print("🔧 HRNGGUI Performance-Analyse")
    print("=" * 50)

    performance_test_data_controller()
    performance_test_serial_simulation()
    identify_bottlenecks()

    print("\n" + "=" * 50)
    print("✅ Performance-Analyse abgeschlossen")
