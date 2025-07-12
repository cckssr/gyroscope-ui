HRNGGUI Code-Struktur und Funktionsweise
========================================

Programmaufbau und Klassenbeziehungen
-------------------------------------

Die HRNGGUI-Anwendung ist eine GUI für die Steuerung und Datenerfassung mit einem GM-Zähler. Sie ist in mehrere Module und Klassen unterteilt, die miteinander interagieren:

1. Hauptklassen und ihre Beziehungen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **MainWindow**: Die zentrale UI-Klasse, die alle anderen Komponenten orchestriert

  - Verwaltet die UI-Elemente
  - Koordiniert die Datenflüsse zwischen Komponenten
  - Kontrolliert die Messungen und deren Status

* **DeviceManager**: Kapselt die Gerätekommunikation und Datenerfassung

  - Stellt eine abstrakte Schnittstelle zum Hardware-Gerät dar
  - Verwaltet Verbindung, Datenerfassung und Fehlerbehandlung
  - Unterstützt sowohl reale Geräte als auch Mock-Geräte für Demonstrationen

* **GMCounter/Arduino**: Hardware-spezifische Klassen für die direkte Kommunikation

  - GMCounter erbt von Arduino für spezifische GM-Zähler-Funktionen
  - Implementiert Low-Level-Kommunikation mit dem Gerät über serielle Schnittstellen

* **DataController**: Verwaltet Messdaten und deren Verarbeitung

  - Speichert und verarbeitet Messwerte
  - Berechnet Statistiken und bereitet Daten für die Visualisierung vor

* **ConnectionWindow**: Dialog zur Auswahl und Verbindung mit einem Gerät

  - Zeigt verfügbare serielle Ports an
  - Ermöglicht die Geräteauswahl und Verbindungsherstellung

* **ControlWidget**: Widget zur Steuerung des GM-Zählers

  - Bietet Benutzeroberfläche für Gerätesteuerung
  - Setzt Einstellungen wie Spannung und Messzeit

* **PlotWidget**: Visualisiert die Messdaten
  - Zeichnet Diagramme der aufgenommenen Daten
  - Unterstützt verschiedene Darstellungsformen (Zeitreihe, Histogramm)

2. Datenfluss und Kommunikation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: 

                        +---------------+
                        
.. csv-table::
   :header-rows: 1
   :widths: auto

|   MainWindow  |

                        +-------+-------+
                                |
              +-----------------+-----------------+
              
.. csv-table::
   :header-rows: 1
   :widths: auto

|                 |                 |

     +--------v------+  +-------v-------+  +-----v-----+
     
.. csv-table::
   :header-rows: 1
   :widths: auto

| DeviceManager |  | DataController |  | PlotWidget |

     +--------+------+  +---------------+  +-----------+
              |
     +--------v------+
     
.. csv-table::
   :header-rows: 1
   :widths: auto

|   GMCounter   |

     +--------+------+
              |
     +--------v------+
     
.. csv-table::
   :header-rows: 1
   :widths: auto

|    Arduino    |

     +---------------+
            |
            v
     Serielle Kommunikation
            |
            v
     +---------------+
     
.. csv-table::
   :header-rows: 1
   :widths: auto

|  Hardware     |

     +---------------+


Verbesserte Implementierung des DeviceManager
---------------------------------------------

Der ``DeviceManager`` wurde umfassend verbessert, um eine robustere und zuverlässigere Datenerfassung zu gewährleisten:

1. Zuverlässige Datenerfassung
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Robuste Thread-Verwaltung**: Sauberes Starten und Beenden von Akquisitions-Threads
* **Fehlertoleranz**: Implementierung von Wiederverbindungslogik und exponentieller Backoff bei Fehlern
* **Statusüberwachung**: Aktive Überprüfung der Verbindungsqualität

2. Verbesserte Fehlererkennung und -behandlung
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Detaillierte Diagnose**: Verbesserte Fehlerprotokolle mit spezifischen Informationen
* **Automatische Wiederverbindung**: Bei Verbindungsabbrüchen wird automatisch versucht, die Verbindung wiederherzustellen
* **Exponentielles Backoff**: Bei wiederholten Fehlern werden die Wartezeiten automatisch angepasst

3. Verbesserte Mock-Daten für Demo-Modus
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Realistische Simulation**: Verbesserte Erzeugung von Mock-Daten mit realistischen Mustern
* **Verschiedene Simulationsmodi**: Normaler Zufallsbereich, sinusförmige Muster und gelegentliche Ausreißer

Datenerfassungs-Threading-Modell
--------------------------------

Der ``DeviceManager`` verwendet ein Thread-basiertes Model für die Datenerfassung:

1. Ein separater Daemon-Thread führt die ``_acquisition_loop``-Methode aus
2. Die Loop liest Daten vom Gerät oder erzeugt Mock-Daten
3. Daten werden über einen Callback-Mechanismus an die UI weitergegeben
4. Fehler werden protokolliert und behandelt, mit automatischen Wiederverbindungsversuchen

Vorteile des verbesserten Thread-Modells:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Nicht-blockierende UI**: Die UI bleibt während der Datenerfassung reaktionsfähig
* **Robustheit gegenüber Fehlern**: Die Anwendung bleibt stabil, auch bei Verbindungsabbrüchen
* **Saubere Beendigung**: Threads werden ordnungsgemäß beendet, ohne hängen zu bleiben

Fehlerbehandlung und Logging
----------------------------

Das System verwendet eine zentrale ``Debug``-Klasse für das Logging:

* **Unterschiedliche Log-Level**: Von Debug über Info bis Error
* **Datei- und Konsolenausgabe**: Logs werden sowohl auf der Konsole als auch in Dateien gespeichert
* **Kontextinformationen**: Log-Einträge enthalten Informationen über den Aufrufer

Zusammenfassung
---------------

Die HRNGGUI-Anwendung ist eine gut strukturierte PySide6-basierte GUI für die Steuerung eines GM-Zählers. Die verbesserten Implementierungen im DeviceManager haben die Robustheit der Datenerfassung erhöht und die Fehlerbehandlung verbessert. Das Programm unterstützt sowohl reale Geräte als auch einen Demonstrationsmodus mit realistischen simulierten Daten.
