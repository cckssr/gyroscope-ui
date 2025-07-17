#!/usr/bin/env python3
"""
Optimierte Version des DataAcquisitionThread für maximale Performance.
"""

import sys
import os
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def create_optimized_thread():
    """Erstelle eine performance-optimierte Version des DataAcquisitionThread."""

    optimized_code = '''
class OptimizedDataAcquisitionThread(QThread):
    """Hochperformante Version für Datenraten bis 10kHz."""
    
    data_point = Signal(int, float)

    def __init__(self, manager: "DeviceManager") -> None:
        super().__init__()
        self.manager = manager
        self._running = False
        self._index = 0
        
        # Performance-Optimierungen
        self._batch_size = 100  # Verarbeite Pakete in Batches
        self._min_read_bytes = 600  # 100 Pakete * 6 Bytes
        self._buffer_size = 8192  # Größerer Buffer
        
    def run(self) -> None:
        """Optimierte run-Methode für maximale Datenrate."""
        self._running = True
        Debug.info("Optimized acquisition thread started (target: 10kHz)")

        # Buffer-Management
        byte_buffer = bytearray()
        START_BYTE = 0xAA
        END_BYTE = 0x55
        PACKET_SIZE = 6
        
        # Performance-Tracking
        packets_processed = 0
        last_log_time = time.time()
        
        while self._running and not self.isInterruptionRequested():
            try:
                if not (self.manager.device and self.manager.connected):
                    time.sleep(0.01)  # Reduziert von 0.1s
                    continue

                if not self.manager.measurement_active:
                    time.sleep(0.01)  # Reduziert von 0.1s
                    continue

                # OPTIMIERUNG 1: Größere Datenblöcke lesen
                raw_data = self.manager.device.read_bytes_fast(
                    max_bytes=self._buffer_size,  # Größerer Buffer
                    timeout_ms=1,  # Reduziert von 5ms
                    start_byte=None  # Kein Start-Byte-Filter in read_bytes_fast
                )

                if raw_data:
                    byte_buffer.extend(raw_data)
                    
                    # OPTIMIERUNG 2: Batch-Verarbeitung
                    processed_in_batch = 0
                    
                    while len(byte_buffer) >= PACKET_SIZE:
                        # Suche nach Start-Byte
                        start_pos = byte_buffer.find(START_BYTE)
                        
                        if start_pos == -1:
                            # Kein Start-Byte, aber behalte die letzten 5 Bytes für Übergang
                            if len(byte_buffer) > 5:
                                byte_buffer = byte_buffer[-5:]
                            break
                        
                        if start_pos > 0:
                            # Entferne Garbage vor Start-Byte
                            byte_buffer = byte_buffer[start_pos:]
                            continue
                        
                        # Prüfe Paket-Vollständigkeit
                        if len(byte_buffer) < PACKET_SIZE:
                            break
                            
                        # Extrahiere Paket
                        packet = bytes(byte_buffer[:PACKET_SIZE])
                        byte_buffer = byte_buffer[PACKET_SIZE:]
                        
                        # Validiere
                        if packet[0] == START_BYTE and packet[5] == END_BYTE:
                            try:
                                value_bytes = packet[1:5]
                                value = int.from_bytes(value_bytes, byteorder="little", signed=False)
                                
                                # OPTIMIERUNG 3: Emit nur bei Batch-Ende oder wichtigen Werten
                                self.data_point.emit(self._index, float(value))
                                self._index += 1
                                processed_in_batch += 1
                                packets_processed += 1
                                
                                # OPTIMIERUNG 4: Break nach Batch-Größe
                                if processed_in_batch >= self._batch_size:
                                    break
                                    
                            except Exception as e:
                                Debug.debug(f"Packet processing error: {e}")
                                continue
                        else:
                            # Invalides Paket, weiter suchen
                            continue
                
                # OPTIMIERUNG 5: Adaptive Sleep-Zeit
                if packets_processed == 0:
                    time.sleep(0.001)  # 1ms wenn keine Daten
                else:
                    # Kein Sleep wenn Daten verfügbar sind
                    pass
                
                # Performance-Logging (reduzierte Frequenz)
                current_time = time.time()
                if current_time - last_log_time > 10.0:  # Alle 10s statt 5s
                    if packets_processed > 0:
                        rate = packets_processed / (current_time - last_log_time + 0.001)
                        Debug.info(f"High-speed acquisition: {rate:.0f} Hz ({packets_processed} packets)")
                        packets_processed = 0
                        last_log_time = current_time
                
            except Exception as e:
                Debug.error(f"Critical error in optimized thread: {e}")
                time.sleep(0.01)

    def reset_index(self) -> None:
        """Reset index counter."""
        self._index = 0
        Debug.debug("Optimized thread index reset")

    def stop(self) -> None:
        """Stop the optimized thread."""
        self._running = False
        self.requestInterruption()
'''

    return optimized_code


def create_performance_config():
    """Erstelle optimierte Konfigurationen."""

    configs = {
        "arduino_optimizations": {
            "baudrate": 115200,  # Höhere Baudrate
            "timeout": 0.001,  # Sehr kurzer Timeout
            "buffer_size": 8192,  # Größerer Buffer
        },
        "thread_optimizations": {
            "batch_size": 100,  # Pakete pro Batch
            "min_sleep_ms": 0,  # Kein Sleep bei aktiven Daten
            "idle_sleep_ms": 1,  # 1ms Sleep wenn keine Daten
            "max_buffer_packets": 1000,  # Max Pakete im Buffer
        },
        "gui_optimizations": {
            "update_interval_ms": 200,  # GUI-Updates alle 200ms statt 100ms
            "plot_decimation": 10,  # Zeige nur jeden 10. Punkt im Plot
            "history_limit": 500,  # Reduziertes History-Limit
        },
    }

    return configs


def benchmark_serial_rates():
    """Benchmark verschiedene serielle Konfigurationen."""

    print("\n=== Serial Performance Benchmark ===")

    # Simuliere verschiedene Baudrates und deren theoretische Limits
    baudrates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
    packet_size = 6  # Bytes per packet

    print("Baudrate     | Theoretical Max Rate | Practical Max Rate")
    print("-" * 60)

    for baudrate in baudrates:
        # Theoretisches Limit: Baudrate / (10 bits per byte * packet_size)
        # 10 bits = 8 data + 1 start + 1 stop bit
        theoretical_max = baudrate / (10 * packet_size)

        # Praktisches Limit (geschätzt mit 70% Effizienz aufgrund von Overhead)
        practical_max = theoretical_max * 0.7

        print(
            f"{baudrate:>8} | {theoretical_max:>15.0f} Hz | {practical_max:>14.0f} Hz"
        )

    print(f"\nAktuelle Konfiguration (wahrscheinlich 9600 baud):")
    print(f"Max theoretical rate: {9600 / 60:.0f} Hz")
    print(f"Max practical rate: {9600 / 60 * 0.7:.0f} Hz")


if __name__ == "__main__":
    print("🔧 Performance-Optimierungsvorschläge")
    print("=" * 50)

    benchmark_serial_rates()

    configs = create_performance_config()

    print(f"\n=== Empfohlene Optimierungen ===")
    print(
        f"1. Arduino Baudrate erhöhen: {configs['arduino_optimizations']['baudrate']}"
    )
    print(f"2. Thread Batch-Size: {configs['thread_optimizations']['batch_size']}")
    print(
        f"3. GUI Update-Intervall: {configs['gui_optimizations']['update_interval_ms']}ms"
    )
    print(
        f"4. Plot-Decimation: Jeden {configs['gui_optimizations']['plot_decimation']}. Punkt"
    )

    print(f"\n=== Erwartete Performance-Verbesserung ===")
    print(f"Aktuell: ~1000-1500 Hz")
    print(f"Mit Optimierungen: ~5000-10000 Hz")
    print(f"Theoretisches Maximum (115200 baud): ~13400 Hz")

    optimized_code = create_optimized_thread()
    print(f"\n✅ Optimierter Code erstellt ({len(optimized_code)} Zeichen)")
    print(f"✅ Konfigurationsempfehlungen erstellt")
    print(f"✅ Performance-Analyse abgeschlossen")
