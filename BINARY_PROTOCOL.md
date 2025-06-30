# Binäres Protokoll für Arduino Fast Data Acquisition

## Protokoll-Spezifikation

### Datenformat

- **Start-Byte:** `0xAA` (170 dezimal)
- **Daten-Bytes:** 4 Bytes (32-bit unsigned integer, little-endian)
- **Gesamtpaketgröße:** 5 Bytes pro Messwert

### Paketstruktur

```
Byte 0: 0xAA (Start-Byte)
Byte 1: Daten LSB (niedrigstes Byte)
Byte 2: Daten Byte 2
Byte 3: Daten Byte 3
Byte 4: Daten MSB (höchstes Byte)
```

### Wertebereich

- **Minimum:** 0 (0x00000000)
- **Maximum:** 4,294,967,295 (0xFFFFFFFF)
- **Typische Werte:** Mikrosekunden-Zeitstempel oder Zählerwerte

## Arduino-Implementierung

### Beispiel Arduino-Code (sender)

```cpp
void sendValue(uint32_t value) {
    Serial.write(0xAA);  // Start-Byte
    Serial.write((byte)(value & 0xFF));         // LSB
    Serial.write((byte)((value >> 8) & 0xFF));  // Byte 2
    Serial.write((byte)((value >> 16) & 0xFF)); // Byte 3
    Serial.write((byte)((value >> 24) & 0xFF)); // MSB
}

void loop() {
    uint32_t microseconds = micros();
    sendValue(microseconds);
    delayMicroseconds(100);  // 10kHz Datenrate
}
```

## Python-Implementierung (Empfänger)

### DataAcquisitionThread

Die `run()` Methode wurde angepasst für:

- **Binäre Paket-Erkennung:** Sucht nach 0xAA Start-Byte
- **Robusten Puffer:** Behandelt unterbrochene/unvollständige Pakete
- **Little-Endian Dekodierung:** `int.from_bytes(bytes, 'little')`
- **Fehlerbehandlung:** Ignoriert ungültige Pakete und synchronisiert neu

### Vorteile gegenüber Textprotokoll

| Aspekt     | Textprotokoll      | Binärprotokoll  |
| ---------- | ------------------ | --------------- |
| Paketgröße | 6-12 Bytes + '\n'  | 5 Bytes fix     |
| CPU-Last   | String-Parsing     | Direkte Bytes   |
| Datenrate  | ~1kHz              | >10kHz          |
| Overhead   | Hoch               | Minimal         |
| Robustheit | Delimiter-abhängig | Start-Byte-Sync |

## Performance-Optimierungen

### Timing

- **read_bytes_fast timeout:** 5ms (reduziert von 10ms)
- **Thread sleep:** 0.5ms (reduziert von 1ms)
- **Maximale Datenrate:** >10kHz theoretisch

### Buffer-Management

- **Byte-weises Suchen:** nach 0xAA Start-Byte
- **Packet-Validation:** Prüfung der 5-Byte-Struktur
- **Automatische Resynchronisation:** bei gestörten Daten

## Beispiel-Pakete

```python
# Wert: 1000 Mikrosekunden
packet = b'\xAA\xE8\x03\x00\x00'
value = int.from_bytes(packet[1:5], 'little')  # = 1000

# Wert: 65535
packet = b'\xAA\xFF\xFF\x00\x00'
value = int.from_bytes(packet[1:5], 'little')  # = 65535

# Maximum: 4294967295
packet = b'\xAA\xFF\xFF\xFF\xFF'
value = int.from_bytes(packet[1:5], 'little')  # = 4294967295
```

## Fehlerbehandlung

### Datenstrom-Synchronisation

1. Suche nach 0xAA in empfangenen Bytes
2. Validiere 5-Byte-Paketlänge
3. Bei Fehlern: Verwerfe Byte und suche weiter
4. Buffer-Overflow-Schutz bei gestörten Daten

### Logging

- **Debug-Level:** Einzelne Pakete mit Hex-Dump
- **Info-Level:** Performance-Statistiken alle 5s
- **Error-Level:** Dekodierung-Fehler mit Paket-Inhalt

## Integration mit GUI

Die Queue-basierte Verarbeitung (100ms GUI-Updates) funktioniert unverändert:

- Binäre Pakete → Queue → Batch-Processing → GUI-Update
- Performance-Monitor zeigt Paket-Rate statt Zeilen-Rate
- Kompatibilität mit bestehender DataController-API

## Test und Validierung

Das binäre Protokoll wurde erfolgreich getestet mit:

- ✅ Einzelpaket-Dekodierung
- ✅ Gestörte Datenströme
- ✅ Start-Byte-Synchronisation
- ✅ Performance unter Last
- ✅ Integration mit read_bytes_fast()

## Migration von Textprotokoll

Für bestehende Arduino-Sketches:

1. Ersetze `Serial.println(value)` durch `sendValue(value)`
2. Keine Änderungen in der Python-GUI erforderlich
3. Automatische Erkennung des Protokolls möglich
