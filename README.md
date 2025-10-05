# Gyroscope GUI

Eine grafische Benutzeroberfläche zur Steuerung und Datenerfassung eines Gyroskops für Rotationsfrequenzmessungen.

## Projektstruktur

Das Projekt verwendet eine modulare Struktur, um die verschiedenen Komponenten sauber zu trennen:

```
gyroscope-ui/
├── main.py             # Hauptprogramm (Einstiegspunkt)
├── start_app.py        # Einfaches Startskript
├── run_tests.py        # Test-Runner für automatisierte Tests
├── integration_test.py # Integrationstests für die Anwendung
├── testplan.md         # Manueller Testplan
├── requirements.txt    # Python Abhängigkeiten
│
├── src/                # Quellcode-Module
│   ├── arduino.py      # GM-Counter Kommunikation
│   ├── config.py       # Zentrale Konfiguration
│   ├── connection.py   # Verbindungsverwaltung
│   ├── data_controller.py # Datenverwaltung und -verarbeitung
│   ├── debug_utils.py  # Debug-Hilfsfunktionen
│   ├── helper_classes.py # Hilfsklassen
│   ├── main_window.py  # Hauptfensterklasse
│   └── plot.py         # Plotting-Funktionalität
│
├── pyqt/               # Qt UI-Definitionen
│   ├── ui_mainwindow.py # Generierte UI-Klasse für das Hauptfenster
│   └── ...             # Weitere UI-Dateien
│
├── logs/               # Logdateien
└── tests/              # Testdateien
    ├── arduino_test.py     # Tests für die Arduino-Klasse
    ├── data_controller_test.py # Tests für den DataController
    └── main_window_test.py # Tests für die MainWindow-Klasse
```

## Installation

1. Abhängigkeiten installieren:

   ```bash
   pip install -r requirements.txt
   ```

2. Anwendung starten:
   ```bash
   ./start_app.py
   ```
   oder
   ```bash
   python start_app.py
   ```

## Verwendung

## Entwicklung

Die Anwendung wurde mit einer sauberen Architektur entwickelt:

- **Model**: `DataController` und andere Datenklassen verwalten die Daten
- **View**: Qt-basierte Benutzeroberfläche
- **Controller**: `MainWindow` und Hilfsklassen steuern den Ablauf

Die `config.py` enthält zentrale Konfigurationsoptionen, die an einer Stelle geändert werden können.

## Tests

Das Projekt enthält umfangreiche Tests, um die Korrektheit der Implementierung sicherzustellen:

### Automatisierte Tests

### Manueller Testplan
