Schnellstart
============

Diese Anleitung bringt Sie schnell zum Einsatz der HRNGGUI.

Installation
------------

.. code-block:: bash

   git clone https://github.com/cckssr/HRNGGUI.git
   cd HRNGGUI
   pip install -r requirements.txt

Erste Schritte
---------------

**1. Demo-Modus (ohne Hardware):**

.. code-block:: bash

   python main.py --demo

**2. Mit GM-Zähler:**

.. code-block:: bash

   python main.py

- Hardware über USB anschließen
- COM-Port wird automatisch erkannt
- Bei Problemen: Einstellungen → Geräteverbindung

Grundfunktionen
---------------

**Datenerfassung starten:**
- "Start" Button in der Hauptansicht
- Messdauer über Einstellungen konfigurierbar
- Echtzeit-Anzeige der eingehenden Daten

**Datenanalyse:**
- Automatische statistische Auswertung
- Verteilungsdiagramme und Histogramme
- Chi-Quadrat-Test für Zufallsqualität

**Datenexport:**
- Datei → Export
- Formate: CSV, JSON, Binär
- Konfigurierbare Metadaten

Konfiguration
-------------

Wichtige Einstellungen in ``config.json``:

.. code-block:: json

   {
     "device": {
       "port": "auto",
       "baudrate": 115200,
       "timeout": 1.0
     },
     "acquisition": {
       "sample_time": 60,
       "buffer_size": 10000
     }
   }

Typische Workflows
-----------------

**Zufallsqualität testen:**
1. Hardware anschließen
2. Messung über 10+ Minuten laufen lassen
3. Statistische Tests durchführen
4. Ergebnisse dokumentieren

**Datensammlung:**
1. Längere Messperiode konfigurieren
2. Automatischen Export aktivieren
3. Überwachung der Datenqualität

Bei Problemen
-------------

- **Keine Verbindung:** COM-Port manuell setzen
- **Fehlerhafte Daten:** Baudrate prüfen (115200)
- **Abstürze:** Debug-Modus aktivieren: ``python main.py --debug``

Weitere Dokumentation: :doc:`troubleshooting` | :doc:`hardware/gm-counter-protocol`

   - Klicken Sie auf "Gerät" → "Verbinden"
   - Wählen Sie den korrekten Port aus
   - Klicken Sie auf "Verbinden"

3. **Verbindung testen**
   - Der Status sollte "Verbunden" anzeigen
   - Geräteinformationen werden angezeigt

Demo-Modus
~~~~~~~~~~

Wenn Sie keinen GM-Zähler haben:

1. **Demo-Modus starten**

   - Starten Sie mit ``python main.py --demo``
   - Oder wählen Sie im Menü "Demo-Modus"

2. **Simulierte Daten**
   - Die Anwendung generiert realistische Testdaten
   - Alle Funktionen sind verfügbar

3. Grundlegende Bedienung
-------------------------

Benutzeroberfläche
~~~~~~~~~~~~~~~~~~

Die Hauptoberfläche besteht aus:

* **Menüleiste**: Dateifunktionen, Einstellungen, Hilfe
* **Gerätestatus**: Verbindungsinformationen
* **Steuerung**: Mess-Parameter und Kontrollen
* **Anzeige**: Aktueller Messwert
* **Diagramm**: Zeitverlauf der Messwerte
* **Statistiken**: Auswertung der Daten

Erste Messung
~~~~~~~~~~~~~

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

4. Datenvisualisierung
----------------------

Zeitverlauf-Diagramm
~~~~~~~~~~~~~~~~~~~~

* **Automatische Skalierung**: Achsen passen sich an
* **Zoom**: Mausrad zum Zoomen
* **Pan**: Mittlere Maustaste zum Verschieben

Histogramm
~~~~~~~~~~

* Wechseln Sie zum "Histogramm"-Tab
* Zeigt die Verteilung der Messwerte
* Binning-Größe ist automatisch optimiert

Datenliste
~~~~~~~~~~

* "Liste"-Tab für tabellarische Ansicht
* Alle Messwerte mit Zeitstempel
* Sortier- und Filterfunktionen

5. Datenverwaltung
------------------

Automatisches Speichern
~~~~~~~~~~~~~~~~~~~~~~~

* Messdaten werden automatisch gespeichert
* Standardpfad: ``~/Documents/GMCounter/``
* Dateiformat: CSV mit Metadaten

Manuelles Speichern
~~~~~~~~~~~~~~~~~~~

1. **Datei** → **Speichern unter**
2. Wählen Sie Speicherort und Namen
3. Fügen Sie Metadaten hinzu:
   - Probenbezeichnung
   - Gruppenname
   - Notizen

Daten laden
~~~~~~~~~~~

* **Datei** → **Öffnen**
* Unterstützte Formate: CSV, JSON
* Automatische Erkennung des Formats

6. Erweiterte Funktionen
------------------------

Kontinuierliche Messung
~~~~~~~~~~~~~~~~~~~~~~~

1. **Wiederholungsmodus** aktivieren
2. **Zählzeit** auf gewünschte Dauer setzen
3. **Start** klicken - Messung läuft kontinuierlich

Statistische Auswertung
~~~~~~~~~~~~~~~~~~~~~~~

* **Mittelwert**: Durchschnitt aller Messwerte
* **Standardabweichung**: Streuung der Werte
* **Min/Max**: Extremwerte
* **Anzahl**: Gesamtzahl der Messungen

Export-Optionen
~~~~~~~~~~~~~~~

* **CSV**: Für Excel und andere Programme
* **JSON**: Für programmatische Verarbeitung
* **PNG**: Diagramm-Export
* **PDF**: Vollständiger Bericht

7. Tipps für Anfänger
---------------------

Erste Messungen
~~~~~~~~~~~~~~~

1. **Kurze Zählzeiten** verwenden (1-10 Sekunden)
2. **Einzelmessungen** für erste Tests
3. **Demo-Modus** zum Kennenlernen der Oberfläche

Gute Messpraxis
~~~~~~~~~~~~~~~

* **Hintergrundstrahlung** zuerst messen
* **Kalibrierung** mit bekannten Quellen
* **Mehrere Messungen** für Statistik
* **Dokumentation** der Messungen

Fehlervermeidung
~~~~~~~~~~~~~~~~

* **Stabile Verbindung** überprüfen
* **Korrekte Spannung** einstellen
* **Ausreichende Zählzeit** wählen
* **Störungen** minimieren

8. Häufige Probleme
-------------------

Verbindungsprobleme
~~~~~~~~~~~~~~~~~~~

**Problem**: Gerät nicht erkannt

**Lösung**:

* USB-Kabel überprüfen
* Treiber installieren
* Port-Rechte prüfen (Linux)

Unrealistische Messwerte
~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Sehr hohe oder niedrige Werte

**Lösung**:

* Spannung kontrollieren
* Verkabelung prüfen
* Demo-Modus zum Vergleich

Langsame Performance
~~~~~~~~~~~~~~~~~~~~

**Problem**: Träge Benutzeroberfläche

**Lösung**:

* Anzahl der Messpunkte reduzieren
* Diagramm-Update-Rate verringern
* Alte Daten löschen

9. Nächste Schritte
-------------------

Nach dem Schnellstart:

1. **`Konfiguration <configuration>`_** anpassen
2. **`Benutzeroberfläche <user-interface>`_** im Detail kennenlernen
3. **`Datenanalyse <data-analysis>`_** vertiefen
4. **`Hardware-Dokumentation <hardware/gm-counter-protocol>`_** studieren

10. Hilfe und Unterstützung
---------------------------

Dokumentation
~~~~~~~~~~~~~

* **`Benutzerhandbuch <user-interface>`_**: Detaillierte Bedienungsanleitung
* **`API-Dokumentation <api>`_**: Für Entwickler
* **`FAQ <faq>`_**: Häufige Fragen und Antworten

Support
~~~~~~~

* **`GitHub Issues <https://github.com/cckssr/HRNGGUI/issues>`_**: Fehlerberichte
* **`Discussions <https://github.com/cckssr/HRNGGUI/discussions>`_**: Fragen und Ideen
* **`Wiki <https://github.com/cckssr/HRNGGUI/wiki>`_**: Community-Dokumentation

Beispiel-Workflow
-----------------

Hier ist ein typischer Arbeitsablauf:

1. **Vorbereitung**

   ````bash
   python main.py --demo
   ````

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
