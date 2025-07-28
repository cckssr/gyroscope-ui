Benutzeroberfläche
====================

Dieses Kapitel beschreibt das Hauptfenster der HRNGGUI und erklärt die Anordnung
der einzelnen Elemente.

Übersicht
----------

.. figure:: img/main_window_placeholder.png
   :alt: Main window overview
   :width: 70%

   Placeholder for a screenshot of the main window.

Das Fenster ist in drei Bereiche unterteilt:

* **Bedienfeld** – Start/Stopp-Schaltflächen, aktuelle Spannung und Messzeit
* **Plot-Bereich** – Live-Diagramm der Messwerte
* **Status- und Exportbereich** – zeigt Statistiken und ermöglicht das Speichern der Daten

Häufige Aktionen
-----------------

*Messung starten*

1. Den GM-Zähler per USB anschließen.
2. Gewünschte Spannung und Messzeit einstellen.
3. :guilabel:`Start` drücken, um die Aufzeichnung zu beginnen.

*Messung beenden*

:guilabel:`Stop` kann jederzeit gedrückt werden. Die Fortschrittsanzeige zeigt
an, wie lange der aktuelle Durchlauf noch dauert.

*Daten speichern*

Mit :guilabel:`Save` öffnet sich ein Dateidialog. Ein Dateiname wird anhand der
ausgewählten Probe und Gruppe vorgeschlagen.

Hinweise zum Design
--------------

Die Benutzeroberfläche ist bewusst schlank gehalten. Die Datenerfassung läuft
in einem Hintergrundthread, der vom ``DataController`` gesteuert wird, während
die Arduino-Schnittstelle alle seriellen Befehle abwickelt. Die GUI leitet nur
Benutzereingaben weiter und zeigt die aufbereiteten Ergebnisse an. Dadurch
bleibt sie auch bei langen Messungen reaktionsfähig.

Platzhalter
-----------

.. figure:: img/control_flow_placeholder.png
   :alt: Control flow between GUI and backend
   :width: 70%

   Platzhalter, der das Zusammenspiel zwischen Hauptfenster, DataController und
   Arduino-Schnittstelle zeigt.

Tastenkürzel
-------------

======================= ==============
Aktion                  Tastenkürzel
======================= ==============
Messung starten       ``Ctrl+R``
Messung stoppen        ``Ctrl+S``
Daten speichern               ``Ctrl+E``
Vollbild umschalten      ``F11``
Hilfe anzeigen               ``F1``
======================= ==============

*** End of file
