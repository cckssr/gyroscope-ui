HRNGGUI-Architektur
====================

Die Anwendung folgt einem schichtbasierten Aufbau, der die Benutzerschnittstelle von der Datenverarbeitung und der Hardwarekommunikation trennt. Dadurch lässt sich das Programm leichter erweitern und warten.

Überblick
---------

1. **GUI-Schicht** – sämtliche Widgets, Dialoge und visuellen Elemente
2. **DataController-Schicht** – sammelt Messwerte und stellt Statistiken bereit
3. **Arduino-Schnittstelle** – übernimmt die serielle Kommunikation mit dem GM-Zähler

.. figure:: img/architecture_overview.png
   :alt: Simplified architecture diagram
   :width: 80%

   Placeholder for a high level architecture diagram.

Begründung
---------

*Die GUI muss auch bei hohem Datenaufkommen reaktionsfähig bleiben.* Daher sammelt das Arduino-Interface Rohdaten und leitet sie in einem Hintergrund-Thread an den ``DataController`` weiter. Dieser puffert die Werte und aktualisiert die GUI-Elemente in regelmäßigen Abständen. Diese Trennung verhindert, dass Hardwareverzögerungen die Oberfläche blockieren und ermöglicht Unit-Tests der Logik ohne grafisches Backend.

Das gleiche Prinzip gilt für Konfigurationsänderungen: Die GUI ändert nur Eigenschaften am ``DataController``, der sie anschließend an das Arduino-Interface überträgt.

Thread-Modell
---------------

* **Hauptthread** – führt alle Qt-Widgets und Timer aus.
* **Acquisition-Thread** – liest Bytes von der seriellen Schnittstelle.
* **Processing-Thread** – optionale aufwändige Berechnungen.

Die Schichten kommunizieren über klar definierte Methoden, um Race Conditions zu vermeiden.

*** End of file
