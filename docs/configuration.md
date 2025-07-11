# Konfiguration

Anpassung der HRNGGUI-Einstellungen für optimale Nutzung.

## Konfigurationsdatei

Die Hauptkonfiguration wird in `config.json` gespeichert:

```json
{
  "debug_level": 1,
  "auto_connect": false,
  "default_port": "",
  "default_voltage": 500,
  "theme": "light",
  "language": "de",
  "save_interval": 300,
  "plot_max_points": 1000
}
```

## Einstellungen

### Debug-Level

- `0`: Keine Debug-Ausgabe
- `1`: Nur Fehler
- `2`: Fehler und Warnungen
- `3`: Alle Meldungen

### Auto-Connect

Automatische Verbindung zum zuletzt verwendeten Gerät beim Start.

### Standard-Spannung

Voreingestellte GM-Spannung in Volt (400-700V).

## Erweiterte Konfiguration

Weitere Einstellungen können über die Benutzeroberfläche angepasst werden.
