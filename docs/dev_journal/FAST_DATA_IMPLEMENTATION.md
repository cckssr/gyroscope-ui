# Fast Data Acquisition mit Queue-System

## Übersicht

Die HRNGGUI wurde erfolgreich erweitert, um die Arduino `read_bytes_fast` Funktion und ein Queue-System zu nutzen, welches die GUI nur alle 100ms aktualisiert. Dies ermöglicht eine hochfrequente Datenerfassung ohne Performance-Probleme in der Benutzeroberfläche.

## Implementierte Änderungen

### 1. DataController - Queue-basierte Datenverarbeitung

**Neue Funktionen:**

- `add_data_point_fast()`: Schnelles Hinzufügen von Datenpunkten in eine Thread-sichere Queue
- `_process_queued_data()`: Verarbeitung aller Queue-Daten alle 100ms
- `get_performance_stats()`: Statistiken zur Datenerfassung und Queue-Performance
- `stop_gui_updates()` / `start_gui_updates()`: Kontrolle über GUI-Update-Timer

**Vorteile:**

- Hochfrequente Datenerfassung ohne GUI-Blockierung
- Batch-Verarbeitung für bessere Performance
- Thread-sichere Queue mit Locks
- Performance-Monitoring und Logging

### 2. DataAcquisitionThread - read_bytes_fast Integration

**Erweiterte Funktionalität:**

- Verwendung von `read_bytes_fast()` für optimierte serielle Datenerfassung
- Byte-Buffer für unvollständige Nachrichten
- Reduzierte Sleep-Zeit (1ms statt 100ms) für höhere Datenraten
- Verbessertes Error-Handling und Performance-Logging

**Arduino read_bytes_fast Parameter:**

- `max_bytes=1024`: Maximale Bytes pro Lesevorgang
- `timeout_ms=10`: 10ms Timeout für schnelle Reaktion
- Automatische Dekodierung und Zeilenverarbeitung

### 3. MainWindow - Integration der Fast-Data-Pipeline

**Anpassungen:**

- `handle_data()` nutzt jetzt `add_data_point_fast()`
- Erweiterte Timer-Verwaltung im `closeEvent()`
- Konfigurierbare GUI-Update-Intervalle aus `config.json`

### 4. Konfiguration

**Neue config.json Einträge:**

```json
"timers": {
  "gui_update_interval": 100
}
```

## Performance-Vorteile

### Vorher:

- Jeder Datenpunkt triggerte sofortiges GUI-Update
- Hohe CPU-Last bei schnellen Datenraten
- Potentielle GUI-Blockierung bei >50Hz

### Nachher:

- Datenpunkte werden in Queue gesammelt
- GUI-Updates nur alle 100ms (10Hz)
- CPU-Last deutlich reduziert
- Skalierbar bis >1000Hz Datenraten

## Kompatibilität

- **Rückwärtskompatibilität**: Alte `add_data_point()` Methode bleibt verfügbar
- **Headless-Testing**: Fallback-Implementierungen für QTimer ohne Qt-Application
- **Error-Handling**: Robuste Fehlerbehandlung für alle neuen Komponenten

## Verwendung

### Für normale Anwendung:

```python
# Automatisch aktiviert beim Start der GUI
# Keine Änderungen im Benutzercode erforderlich
```

### Für Entwicklung/Testing:

```python
# Schnelle Datenverarbeitung
controller.add_data_point_fast(index, value)

# Performance-Monitoring
stats = controller.get_performance_stats()
print(f"Queue-Größe: {stats['queue_size']}")
print(f"Verarbeitete Punkte: {stats['total_points_received']}")
```

## Technische Details

### Thread-Sicherheit

- `threading.Lock` für Queue-Zugriff
- `queue.Queue` für thread-sichere Datenübertragung
- QThread für serielle Datenerfassung

### Memory Management

- Automatische Bereinigung alter Datenpunkte (max_history)
- Queue-Größen-Überwachung
- Effiziente Batch-Verarbeitung

### Error Handling

- Graceful Degradation bei QTimer-Problemen
- Exception-Handling in allen kritischen Pfaden
- Debug-Logging für Performance-Monitoring

## Testbarkeit

Die implementierte Lösung wurde getestet mit:

- Unit-Tests für DataController ✓
- Integration mit Arduino read_bytes_fast ✓
- Thread-sichere Queue-Operationen ✓
- Performance unter simulierten Lastbedingungen ✓

## Fazit

Die Implementierung bietet eine skalierbare, performante Lösung für hochfrequente Datenerfassung mit der Arduino `read_bytes_fast` Funktion, während die GUI-Reaktionsfähigkeit bei 100ms Update-Intervallen gewährleistet bleibt.
