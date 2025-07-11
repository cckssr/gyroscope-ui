# Schnellstart

Diese Anleitung führt Sie durch die ersten Schritte mit HRNGGUI.

## Voraussetzungen

- HRNGGUI ist [installiert](installation.md)
- Ein GM-Zähler ist verfügbar (oder Demo-Modus)

## 1. Anwendung starten

### Kommandozeile

```bash
# Normale Ausführung
python main.py

# Demo-Modus (ohne Hardware)
python main.py --demo

# Debug-Modus
python main.py --debug
```

### Desktop-Integration

Nach der Installation sollte HRNGGUI in Ihrem Anwendungsmenü verfügbar sein.

## 2. Erste Verbindung

### Mit Hardware

1. **Gerät anschließen**

   - Verbinden Sie Ihren GM-Zähler per USB
   - Warten Sie, bis das Gerät erkannt wird

2. **Verbindung herstellen**

   - Klicken Sie auf "Gerät" → "Verbinden"
   - Wählen Sie den korrekten Port aus
   - Klicken Sie auf "Verbinden"

3. **Verbindung testen**
   - Der Status sollte "Verbunden" anzeigen
   - Geräteinformationen werden angezeigt

### Demo-Modus

Wenn Sie keinen GM-Zähler haben:

1. **Demo-Modus starten**

   - Starten Sie mit `python main.py --demo`
   - Oder wählen Sie im Menü "Demo-Modus"

2. **Simulierte Daten**
   - Die Anwendung generiert realistische Testdaten
   - Alle Funktionen sind verfügbar

## 3. Grundlegende Bedienung

### Benutzeroberfläche

Die Hauptoberfläche besteht aus:

- **Menüleiste**: Dateifunktionen, Einstellungen, Hilfe
- **Gerätestatus**: Verbindungsinformationen
- **Steuerung**: Mess-Parameter und Kontrollen
- **Anzeige**: Aktueller Messwert
- **Diagramm**: Zeitverlauf der Messwerte
- **Statistiken**: Auswertung der Daten

### Erste Messung

1. **Parameter einstellen**

   - Spannung: 500-600V (typisch)
   - Zählzeit: 10 Sekunden für erste Tests
   - Modus: "Einzel" für eine Messung

2. **Messung starten**

   - Klicken Sie auf "Start"
   - Beobachten Sie den Fortschritt
   - Warten Sie auf das Ergebnis

3. **Ergebnisse anzeigen**
   - Aktueller Wert im LCD-Display
   - Zeitverlauf im Diagramm
   - Statistiken im unteren Bereich

## 4. Datenvisualisierung

### Zeitverlauf-Diagramm

- **Automatische Skalierung**: Achsen passen sich an
- **Zoom**: Mausrad zum Zoomen
- **Pan**: Mittlere Maustaste zum Verschieben

### Histogramm

- Wechseln Sie zum "Histogramm"-Tab
- Zeigt die Verteilung der Messwerte
- Binning-Größe ist automatisch optimiert

### Datenliste

- "Liste"-Tab für tabellarische Ansicht
- Alle Messwerte mit Zeitstempel
- Sortier- und Filterfunktionen

## 5. Datenverwaltung

### Automatisches Speichern

- Messdaten werden automatisch gespeichert
- Standardpfad: `~/Documents/GMCounter/`
- Dateiformat: CSV mit Metadaten

### Manuelles Speichern

1. **Datei** → **Speichern unter**
2. Wählen Sie Speicherort und Namen
3. Fügen Sie Metadaten hinzu:
   - Probenbezeichnung
   - Gruppenname
   - Notizen

### Daten laden

- **Datei** → **Öffnen**
- Unterstützte Formate: CSV, JSON
- Automatische Erkennung des Formats

## 6. Erweiterte Funktionen

### Kontinuierliche Messung

1. **Wiederholungsmodus** aktivieren
2. **Zählzeit** auf gewünschte Dauer setzen
3. **Start** klicken - Messung läuft kontinuierlich

### Statistische Auswertung

- **Mittelwert**: Durchschnitt aller Messwerte
- **Standardabweichung**: Streuung der Werte
- **Min/Max**: Extremwerte
- **Anzahl**: Gesamtzahl der Messungen

### Export-Optionen

- **CSV**: Für Excel und andere Programme
- **JSON**: Für programmatische Verarbeitung
- **PNG**: Diagramm-Export
- **PDF**: Vollständiger Bericht

## 7. Tipps für Anfänger

### Erste Messungen

1. **Kurze Zählzeiten** verwenden (1-10 Sekunden)
2. **Einzelmessungen** für erste Tests
3. **Demo-Modus** zum Kennenlernen der Oberfläche

### Gute Messpraxis

- **Hintergrundstrahlung** zuerst messen
- **Kalibrierung** mit bekannten Quellen
- **Mehrere Messungen** für Statistik
- **Dokumentation** der Messungen

### Fehlervermeidung

- **Stabile Verbindung** überprüfen
- **Korrekte Spannung** einstellen
- **Ausreichende Zählzeit** wählen
- **Störungen** minimieren

## 8. Häufige Probleme

### Verbindungsprobleme

**Problem**: Gerät nicht erkannt

**Lösung**:

- USB-Kabel überprüfen
- Treiber installieren
- Port-Rechte prüfen (Linux)

### Unrealistische Messwerte

**Problem**: Sehr hohe oder niedrige Werte

**Lösung**:

- Spannung kontrollieren
- Verkabelung prüfen
- Demo-Modus zum Vergleich

### Langsame Performance

**Problem**: Träge Benutzeroberfläche

**Lösung**:

- Anzahl der Messpunkte reduzieren
- Diagramm-Update-Rate verringern
- Alte Daten löschen

## 9. Nächste Schritte

Nach dem Schnellstart:

1. **[Konfiguration](configuration.md)** anpassen
2. **[Benutzeroberfläche](user-interface.md)** im Detail kennenlernen
3. **[Datenanalyse](data-analysis.md)** vertiefen
4. **[Hardware-Dokumentation](hardware/gm-counter-protocol.md)** studieren

## 10. Hilfe und Unterstützung

### Dokumentation

- **[Benutzerhandbuch](user-interface.md)**: Detaillierte Bedienungsanleitung
- **[API-Dokumentation](api/README.md)**: Für Entwickler
- **[FAQ](faq.md)**: Häufige Fragen und Antworten

### Support

- **[GitHub Issues](https://github.com/cckssr/HRNGGUI/issues)**: Fehlerberichte
- **[Discussions](https://github.com/cckssr/HRNGGUI/discussions)**: Fragen und Ideen
- **[Wiki](https://github.com/cckssr/HRNGGUI/wiki)**: Community-Dokumentation

## Beispiel-Workflow

Hier ist ein typischer Arbeitsablauf:

1. **Vorbereitung**

   ```bash
   python main.py --demo
   ```

2. **Konfiguration**

   - Spannung: 520V
   - Zählzeit: 30 Sekunden
   - Modus: Wiederholung

3. **Messung**

   - 10 Messungen durchführen
   - Ergebnisse beobachten
   - Statistiken notieren

4. **Analyse**

   - Histogramm betrachten
   - Ausreißer identifizieren
   - Trends erkennen

5. **Dokumentation**
   - Daten speichern
   - Diagramm exportieren
   - Ergebnisse dokumentieren

Viel Erfolg mit HRNGGUI!
