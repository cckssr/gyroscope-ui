Benutzeroberfläche
==================

Übersicht der HRNGGUI-Bedienelemente für effiziente Nutzung.

Hauptfenster-Layout
-------------------

**Menüleiste:**
- **Datei**: Export, Konfiguration laden/speichern
- **Geräte**: Verbindungseinstellungen, COM-Port Auswahl
- **Ansicht**: Diagramm-Optionen, Layout anpassen
- **Extras**: Erweiterte Einstellungen

**Steuerungsbereich (links):**
- Verbindungsstatus mit grün/rot Indikator
- Start/Stop Buttons für Datenerfassung
- Aktuelle Messrate (counts/min)
- Hardware-Parameter (Spannung, Timeout)

**Datenvisualisierung (zentral):**
- Echtzeit-Diagramm der Zählrate
- Histogramm der Zeitintervalle
- Statistische Übersicht (Mittelwert, Standardabweichung)
- Chi-Quadrat-Test Ergebnisse

**Datenexport (rechts):**
- Raw-Data Anzeige
- Export-Buttons (CSV, JSON, Binary)
- Datei-Info (Größe, Zeitstempel)

Bedienelemente
--------------

**Datenerfassung starten:**
1. Hardware anschließen → Status wird grün
2. "Start" klicken → Echtzeit-Erfassung beginnt
3. Gewünschte Dauer abwarten
4. "Stop" oder automatisches Ende

**Analyse-Tools:**
- **Live-Statistik**: Automatische Berechnung während Messung
- **Qualitätstests**: Chi-Quadrat, Kolmogorov-Smirnov
- **Verteilungsdiagramme**: Histogramme mit konfigurierbaren Bins

**Konfiguration:**
- **Sampling-Rate**: Einstellbar von 1-1000 Hz
- **Puffergröße**: Memory-Management für lange Messungen
- **Export-Format**: Metadaten und Komprimierung

Tastenkombinationen
-------------------

========== ================
Funktion   Shortcut
========== ================
Start      ``Ctrl+R``
Stop       ``Ctrl+S``
Export     ``Ctrl+E``
Hilfe      ``F1``
Vollbild   ``F11``
========== ================

Troubleshooting
---------------

**Grauer Verbindungsstatus:**
- COM-Port in Geräteeinstellungen überprüfen
- USB-Kabel und Hardware-Verbindung testen

**Keine Daten trotz grünem Status:**
- Baudrate prüfen (Standard: 115200)
- Protokoll-Einstellungen überprüfen

**Diagramm bleibt leer:**
- Mindest-Sampling-Zeit abwarten (1-2 Sekunden)
- Debug-Modus für detaillierte Logs aktivieren
~~~~~~~~~~~~~~~

Unten im Fenster:

* **Verbindungsstatus**
* **Aktuelle Aktivität**
* **Fehlermeldungen**

Bedienelemente
--------------

Schaltflächen
~~~~~~~~~~~~~

* **Start**: Messung beginnen
* **Stopp**: Messung beenden
* **Zurücksetzen**: Daten löschen
* **Verbinden**: Geräteverbindung herstellen

Eingabefelder
~~~~~~~~~~~~~

* **Spannung**: 400-700V
* **Port**: Auswahl des seriellen Ports
* **Suffix**: Benutzerdefinierte Bezeichnung

Auswahlfelder
~~~~~~~~~~~~~

* **Zählzeit**: Vordefinierte Zeiträume
* **Modus**: Einzel oder Wiederholung
* **Gruppe**: Praktikumsgruppe

Tastenkombinationen
-------------------

* **Ctrl+N**: Neue Messung
* **Ctrl+S**: Speichern
* **Ctrl+Q**: Beenden
* **F1**: Hilfe
* **F11**: Vollbild

Customization
-------------

Die Benutzeroberfläche kann angepasst werden:

* **Themen**: Hell/Dunkel
* **Layout**: Dockable Widgets
* **Sprache**: Deutsch/Englisch
