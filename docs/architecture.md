# Architektur der HRNGGUI

Die HRNGGUI-Anwendung folgt einer modularen Architektur, die eine klare Trennung von Verantwortlichkeiten und eine einfache Erweiterbarkeit ermöglicht.

## Überblick

Die Anwendung ist in mehrere Schichten unterteilt:

1. **Präsentationsschicht** - Benutzeroberfläche (UI)
2. **Anwendungsschicht** - Geschäftslogik
3. **Datenschicht** - Datenverarbeitung und -speicherung
4. **Hardware-Abstraktionsschicht** - Gerätekommunikation

## Architekturdiagramm

```text
┌─────────────────────────────────────────────────────┐
│                Benutzeroberfläche                   │
│                   (MainWindow)                      │
└─────────────────┬───────────────────────────────────┘
                  │
     ┌────────────┼────────────┐
     │            │            │
     ▼            ▼            ▼
┌─────────┐ ┌─────────────┐ ┌─────────┐
│ Device  │ │    Data     │ │  Plot   │
│Manager  │ │ Controller  │ │ Widget  │
└─────────┘ └─────────────┘ └─────────┘
     │            │            │
     ▼            ▼            ▼
┌─────────┐ ┌─────────────┐ ┌─────────┐
│GM Counter│ │Data Storage │ │Matplotlib│
│         │ │& Processing │ │ Backend │
└─────────┘ └─────────────┘ └─────────┘
     │
     ▼
┌─────────┐
│ Arduino │
│Interface│
└─────────┘
     │
     ▼
┌─────────┐
│Hardware │
│ (USB)   │
└─────────┘
```

**Datenfluss:**

1. Hardware sendet Daten über USB → Arduino Interface
2. Arduino Interface verarbeitet Rohdaten → GM Counter
3. GM Counter strukturiert Daten → Data Controller
4. Data Controller speichert und verarbeitet → Plot Widget
5. Plot Widget visualisiert → Benutzeroberfläche

## Komponenten-Übersicht

### Präsentationsschicht

#### MainWindow

- **Zweck**: Zentrale Koordination der Benutzeroberfläche
- **Verantwortlichkeiten**:
  - Orchestrierung aller UI-Komponenten
  - Event-Handling für Benutzerinteraktionen
  - Statusverwaltung der Anwendung
- **Abhängigkeiten**: DataController, DeviceManager, PlotWidget

#### PlotWidget

- **Zweck**: Visualisierung von Messdaten
- **Verantwortlichkeiten**:
  - Echtzeitdarstellung von Daten
  - Verschiedene Diagrammtypen (Zeitreihe, Histogramm)
  - Interaktive Features (Zoom, Pan)
- **Technologie**: Matplotlib mit Qt-Backend

### Anwendungsschicht

#### DataController

- **Zweck**: Zentrale Datenverwaltung
- **Verantwortlichkeiten**:
  - Speicherung von Messdaten
  - Statistische Berechnungen
  - Datenvalidierung
  - Export-Funktionen
- **Design Pattern**: Observer Pattern für UI-Updates

#### DeviceManager

- **Zweck**: Abstrakte Geräteverwaltung
- **Verantwortlichkeiten**:
  - Geräteverbindungen verwalten
  - Datenerfassung koordinieren
  - Fehlerbehandlung und Wiederverbindung
  - Mock-Daten für Demo-Modus
- **Threading**: Separate Threads für Datenerfassung

### Hardware-Abstraktionsschicht

#### GMCounter

- **Zweck**: Spezifische GM-Zähler-Funktionalität
- **Verantwortlichkeiten**:
  - Implementierung des GM-Zähler-Protokolls
  - Gerätekonfiguration
  - Datenabfrage
- **Vererbung**: Erbt von Arduino-Klasse

#### Arduino

- **Zweck**: Grundlegende Arduino-Kommunikation
- **Verantwortlichkeiten**:
  - Serielle Kommunikation
  - Verbindungsmanagement
  - Basis-Konfiguration
- **Protokoll**: Seriell über USB/UART

## Design Patterns

### Observer Pattern

- **Verwendung**: DataController → UI-Komponenten
- **Zweck**: Automatische UI-Updates bei Datenänderungen
- **Implementierung**: Callback-basiert

### Strategy Pattern

- **Verwendung**: DeviceManager → Gerätekommunikation
- **Zweck**: Austauschbare Gerätetypen (echte Geräte vs. Mock)
- **Implementierung**: Polymorphie über Vererbung

### Factory Pattern

- **Verwendung**: Geräteerstellung
- **Zweck**: Dynamische Geräteerstellung basierend auf Konfiguration

## Threading-Modell

### Hauptthread (UI-Thread)

- Benutzeroberfläche
- Event-Handling
- Kurze Berechnungen

### Datenerfassungs-Thread

- Kontinuierliche Datenerfassung
- Gerätekommunikation
- Fehlerbehandlung

### Verarbeitungs-Thread

- Statistische Berechnungen
- Export-Operationen
- Datenverarbeitung

## Fehlerbehandlung

### Ebenen der Fehlerbehandlung

1. **Hardware-Ebene**:

   - Timeout-Behandlung
   - Verbindungsabbrüche
   - Datenkorruption

2. **Anwendungsebene**:

   - Datenvalidierung
   - Benutzerfehlererkennung
   - Zustandsinkonsistenzen

3. **UI-Ebene**:
   - Benutzerfeedback
   - Fehlervisualisierung
   - Wiederherstellungsoptionen

### Logging-System

- **Zentrale Debug-Klasse**: Einheitliches Logging
- **Log-Level**: Debug, Info, Warning, Error, Critical
- **Ausgabe**: Konsole und Datei
- **Kontext**: Automatische Aufrufer-Identifikation

## Konfiguration

### Konfigurationsdateien

- `config.json`: Anwendungseinstellungen
- `radioactive_samples.json`: Probendaten
- `book.toml`: Dokumentationskonfiguration

### Konfigurationsverwaltung

- Zentrale Konfigurationsklasse
- Umgebungsvariablen-Unterstützung
- Validierung von Konfigurationswerten

## Erweiterbarkeit

### Plugin-System

- Modulare Geräteunterstützung
- Erweiterbare Datenexport-Formate
- Anpassbare Visualisierungen

### API-Design

- Klare Schnittstellen
- Dokumentierte APIs
- Versionierung

## Performance-Optimierungen

### Datenverarbeitung

- Ringpuffer für Echtzeitdaten
- Lazy Loading für große Datensätze
- Caching von Berechnungen

### UI-Performance

- Effiziente Plot-Updates
- Debouncing für UI-Events
- Virtuelle Listen für große Datenmengen

## Sicherheit

### Datenschutz

- Keine persönlichen Daten gespeichert
- Lokale Datenverarbeitung
- Konfigurierbare Datenaufbewahrung

### Robustheit

- Eingabevalidierung
- Sichere Dateioperation
- Graceful Degradation

## Deployment

### Packaging

- Python-Packaging mit setuptools
- Abhängigkeits-Management
- Plattformspezifische Builds

### Installation

- Pip-basierte Installation
- Virtuelle Umgebungen
- System-Integration

## Wartung

### Code-Qualität

- Statische Code-Analyse
- Einheitliche Coding-Standards
- Dokumentation

### Testing

- Unit-Tests für Kernkomponenten
- Integrationstests
- Mock-basierte Tests

Diese Architektur ermöglicht es, die HRNGGUI-Anwendung effizient zu entwickeln, zu warten und zu erweitern, während sie gleichzeitig eine robuste und benutzerfreundliche Erfahrung bietet.
