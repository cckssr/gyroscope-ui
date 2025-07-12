Datenanalyse & Konfiguration
============================

HRNGGUI bietet umfangreiche Tools zur Analyse der Zufallsqualität und konfigurierbare Parameter für verschiedene Anwendungen.

Statistische Analyse
--------------------

**Echtzeitstatistiken:**
- **Zählrate** (counts/min): Aktivität der radioaktiven Quelle
- **Mittelwert**: Durchschnittliche Zeitintervalle zwischen Events
- **Standardabweichung**: Variabilität der Messwerte
- **Varianz**: Quadrat der Standardabweichung

**Qualitätstests:**
- **Chi-Quadrat-Test**: Prüft Gleichverteilung (p > 0.05 = gut)
- **Kolmogorov-Smirnov**: Testet gegen Referenzverteilung
- **Autokorrelation**: Erkennt systematische Abhängigkeiten

**Visualisierung:**
- **Zeitreihe**: Live-Plot der Zählrate
- **Histogramm**: Verteilung der Zeitintervalle
- **Scatter-Plot**: Aufeinanderfolgende Werte (Korrelationstest)

Konfiguration
-------------

Hauptkonfiguration in ``config.json``:

.. code-block:: json

   {
     "device": {
       "port": "auto",           // COM-Port (auto = automatisch)
       "baudrate": 115200,       // Übertragungsrate
       "timeout": 1.0,           // Verbindungs-Timeout
       "protocol": "standard"    // Protokoll-Typ
     },
     "acquisition": {
       "sample_time": 60,        // Messzeit in Sekunden
       "buffer_size": 10000,     // Max. Datenpunkte im Memory
       "auto_save": true,        // Automatisches Speichern
       "save_interval": 300      // Speichern alle 5 Min
     },
     "analysis": {
       "update_rate": 1.0,       // Diagramm-Update (Hz)
       "histogram_bins": 50,     // Anzahl Histogram-Balken
       "statistical_window": 1000 // Punkte für rolling stats
     }
   }

**Hardware-spezifische Einstellungen:**

Arduino GM-Zähler:
  ``"protocol": "arduino", "baudrate": 9600``

Frederiksen Scientific:
  ``"protocol": "frederiksen", "baudrate": 115200``

Benutzerdefiniert:
  ``"protocol": "custom", "delimiter": "\n"``

Datenexport
-----------

**CSV-Format (Standard):**
- Zeitstempel, Zählwert, Intervall
- Metadaten im Header
- Kompatibel mit Excel, Python, R

**JSON-Format:**
- Strukturierte Daten mit Metadaten
- Programmatischer Zugriff
- Konfigurationsinformationen enthalten

**Binär-Format:**
- Kompakte Speicherung für große Datenmengen
- Schneller I/O
- NumPy-kompatibel

Qualitätsbewertung
-----------------

**Gute Zufallsqualität:**
- Chi-Quadrat p-Wert > 0.05
- Gleichmäßiges Histogramm
- Keine erkennbaren Muster im Scatter-Plot
- Autokorrelation nahe 0

**Problematische Signale:**
- Periodische Schwankungen → Elektrische Störungen
- Clustered Events → Defekte Hardware
- Systematische Trends → Umgebungseinflüsse

**Optimierungstipps:**
- Längere Messzeiten für stabilere Statistiken
- Abschirmung gegen elektromagnetische Störungen
- Temperaturstabile Umgebung
- Regelmäßige Kalibration der Hardware
