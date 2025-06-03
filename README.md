# HRNGGUI - Geiger-Müller Counter GUI

Eine grafische Benutzeroberfläche zur Steuerung und Datenerfassung eines Geiger-Müller-Zählrohrs für Zufallszahlengenerierung.

## Projektstruktur

Das Projekt verwendet eine modulare Struktur, um die verschiedenen Komponenten sauber zu trennen:

```
HRNGGUI/
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

1. Nach dem Start wird ein Verbindungsdialog angezeigt, in dem Sie den seriellen Port auswählen können.

2. Im Hauptfenster können Sie:
   - Die Messparameter (Spannung, Zähldauer, etc.) einstellen
   - Messungen starten und stoppen
   - Messdaten in Echtzeit anzeigen
   - Statistiken zur laufenden Messung anzeigen
   - Messdaten als CSV exportieren

## Entwicklung

Die Anwendung wurde mit einer sauberen Architektur entwickelt:

- **Model**: `DataController` und andere Datenklassen verwalten die Daten
- **View**: Qt-basierte Benutzeroberfläche
- **Controller**: `MainWindow` und Hilfsklassen steuern den Ablauf

Die `config.py` enthält zentrale Konfigurationsoptionen, die an einer Stelle geändert werden können.

## Tests

Das Projekt enthält umfangreiche Tests, um die Korrektheit der Implementierung sicherzustellen:

### Automatisierte Tests

Die Tests können mit dem Test-Runner ausgeführt werden:

```bash
python run_tests.py
```

Verfügbare Tests:

- **Unit-Tests**: Testen einzelne Komponenten isoliert

  - `arduino_test.py`: Tests für die Arduino-Kommunikation
  - `data_controller_test.py`: Tests für die Datenverwaltung
  - `main_window_test.py`: Tests für das Hauptfenster

- **Integrationstests**: Testen das Zusammenspiel mehrerer Komponenten
  - `integration_test.py`: Überprüft das Zusammenspiel der Hauptkomponenten

### Manueller Testplan

Der Datei `testplan.md` enthält einen strukturierten Plan für manuelle Tests mit verschiedenen Testszenarien und Checklisten. Dieser sollte nach größeren Änderungen durchlaufen werden, um sicherzustellen, dass alle Funktionen korrekt arbeiten.

Zur komfortablen Durchführung dieser Checkliste kann das Skript `manual_checklist.py` verwendet werden:

```bash
python manual_checklist.py --file tests/testplan.md --output checklist_results.json
```

Das Skript liest alle Aufgaben aus der Markdown-Datei, fragt sie nacheinander ab und speichert die Ergebnisse im angegebenen JSON-File.
