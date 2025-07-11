# Fehlerbehebung

Lösungen für häufige Probleme mit HRNGGUI.

## Installationsprobleme

### Python-Abhängigkeiten

```bash
# Fehlende Module installieren
pip install PySide6 matplotlib numpy pyserial
```

### Berechtigungen (Linux)

```bash
# Benutzer zur dialout-Gruppe hinzufügen
sudo usermod -a -G dialout $USER
# Neu anmelden erforderlich
```

## Verbindungsprobleme

### Gerät nicht gefunden

1. Prüfen Sie die USB-Verbindung
2. Installieren Sie die Arduino-Treiber
3. Überprüfen Sie verfügbare Ports:

```bash
python -c "import serial.tools.list_ports; print(list(serial.tools.list_ports.comports()))"
```

### Timeout-Fehler

- Verringern Sie die Baudrate
- Erhöhen Sie den Timeout-Wert
- Prüfen Sie die Kabelverbindung

## Anwendungsprobleme

### Anwendung startet nicht

```bash
# Debug-Modus aktivieren
python main.py --debug
```

### Keine Daten empfangen

1. Prüfen Sie die Geräteeinstellungen
2. Testen Sie im Demo-Modus
3. Überprüfen Sie die Protokoll-Konfiguration

## Logs und Debugging

Log-Dateien finden Sie unter:

- **Windows**: `%APPDATA%\HRNGGUI\logs\`
- **macOS**: `~/Library/Application Support/HRNGGUI/logs/`
- **Linux**: `~/.config/HRNGGUI/logs/`
