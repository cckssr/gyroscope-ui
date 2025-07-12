HRNGGUI - Hardware Random Number Generator GUI
==============================================

**HRNGGUI** ist eine spezialisierte Anwendung zur Datenerfassung und -analyse von Hardware-Zufallszahlengeneratoren mit Geiger-Müller-Zählern.

Hauptfunktionen
===============

* **Echtzeit-Datenerfassung** von GM-Zählern über serielle Schnittstelle
* **Statistische Analyse** zur Bewertung der Zufallsqualität
* **Grafische Visualisierung** von Messdaten und Verteilungen
* **Datenexport** in verschiedenen Formaten (CSV, JSON, Binary)
* **Konfigurierbare Hardware-Protokolle** für verschiedene GM-Zähler-Modelle

.. toctree::
   :maxdepth: 2
   :caption: Projektdokumentation

   quickstart
   hardware/gm-counter-protocol
   hardware/arduino-integration
   architecture
   api
   
.. toctree::
   :maxdepth: 1
   :caption: Bedienung

   user-interface
   data-analysis
   
.. toctree::
   :maxdepth: 1
   :caption: Support

   faq
   troubleshooting

Schnellstart
============

1. **Installation:**

   .. code-block:: bash
   
      git clone https://github.com/cckssr/HRNGGUI.git
      cd HRNGGUI
      pip install -r requirements.txt

2. **Hardware vorbereiten:**
   - GM-Zähler per USB anschließen
   - COM-Port in Konfiguration eintragen

3. **Anwendung starten:**

   .. code-block:: bash
   
      python main.py

   Für Demo ohne Hardware:

   .. code-block:: bash
   
      python main.py --demo

Systemvoraussetzungen
=====================

* Python 3.10+
* PySide6, Matplotlib, PySerial
* USB-Port für GM-Zähler

Über das Projekt
================

HRNGGUI wurde für wissenschaftliche Anwendungen entwickelt, die echte Zufallszahlen aus radioaktivem Zerfall benötigen. Die Anwendung bietet präzise Datenerfassung und umfangreiche Analysetools zur Bewertung der Zufallsqualität.

**Autor:** Cedric Kessler | **Lizenz:** MIT | **GitHub:** `HRNGGUI Repository <https://github.com/cckssr/HRNGGUI>`_
