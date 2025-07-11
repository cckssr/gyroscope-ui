# HRNGGUI - Geiger-Müller Counter GUI

Eine grafische Benutzeroberfläche zur Steuerung und Datenerfassung eines Geiger-Müller-Zählrohrs für Hardware-Zufallszahlengenerierung (HRNG).

## Überblick

Die HRNGGUI ist eine in Python entwickelte Anwendung, die eine benutzerfreundliche grafische Oberfläche für die Steuerung von Geiger-Müller-Zählern bereitstellt. Sie ermöglicht die Erfassung, Visualisierung und Analyse von Strahlungsdaten für wissenschaftliche Experimente und Zufallszahlengenerierung.

## Hauptfunktionen

- **Gerätesteuerung**: Vollständige Kontrolle über GM-Zähler-Parameter
- **Echtzeitvisualisierung**: Live-Plots der Messdaten
- **Datenanalyse**: Statistische Auswertung der erfassten Daten
- **Export**: Speichern der Daten in verschiedenen Formaten
- **Simulationsmodus**: Demo-Modus für Tests ohne Hardware

## Technische Daten

- **Sprache**: Python 3.10+
- **GUI-Framework**: PySide6 (Qt6)
- **Unterstützte Plattformen**: Windows, macOS, Linux
- **Kommunikation**: Serielle Schnittstelle (USB/UART)

## Schnellstart

1. **Installation**: Laden Sie die neueste Version herunter
2. **Abhängigkeiten**: Installieren Sie die erforderlichen Python-Pakete
3. **Geräteverbindung**: Schließen Sie Ihren GM-Zähler an
4. **Starten**: Führen Sie die Anwendung aus

Weitere Details finden Sie in der [Installationsanleitung](installation.md).

## Projektstruktur

```text
HRNGGUI/
├── src/                    # Quellcode
│   ├── main_window.py      # Hauptfenster
│   ├── data_controller.py  # Datenverwaltung
│   ├── plot.py            # Visualisierung
│   ├── arduino.py         # Hardware-Kommunikation
│   └── ...
├── docs/                   # Dokumentation
├── tests/                  # Testdateien
├── pyqt/                   # UI-Definitionen
└── logs/                   # Logdateien
```

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Weitere Informationen finden Sie in der [Lizenzdatei](license.md).

## Unterstützung

Bei Fragen oder Problemen:

- Öffnen Sie ein Issue im GitHub-Repository
- Konsultieren Sie die [FAQ](faq.md)
- Prüfen Sie die [Fehlerbehebung](troubleshooting.md)
