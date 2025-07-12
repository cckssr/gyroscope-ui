Troubleshooting
===============

Schnelle Lösungen für häufige HRNGGUI-Probleme.

Verbindungsprobleme
------------------

**"Kein Gerät gefunden" / Grauer Status:**

.. code-block:: bash

   # Verfügbare Ports anzeigen
   python -c "import serial.tools.list_ports; [print(p) for p in serial.tools.list_ports.comports()]"

**Lösungen:**
- USB-Kabel tauschen
- Anderen USB-Port verwenden  
- Treiber installieren (Windows: Arduino IDE, Linux: ``sudo usermod -a -G dialout $USER``)
- Port manuell in config.json setzen: ``"port": "/dev/ttyUSB0"``

**Verbindung bricht ab:**
- Timeout erhöhen: ``"timeout": 5.0``
- Baudrate reduzieren: ``"baudrate": 9600``
- Auto-Reconnect aktivieren: ``"auto_reconnect": true``

Datenprobleme
-------------

**Keine Messwerte trotz Verbindung:**
- Hardware mit Serial Monitor testen
- Protokoll-Einstellung prüfen (arduino/frederiksen/custom)
- Debug-Modus: ``python main.py --debug``

**Unrealistische Werte:**
- Kalibrierungsfaktor anpassen
- HV-Spannung prüfen (~400V)
- Elektrische Störquellen eliminieren

**Datenverlust bei langen Messungen:**
- Puffergröße erhöhen: ``"buffer_size": 50000``
- Auto-Save aktivieren: ``"auto_save": true``  
- Update-Rate reduzieren: ``"update_rate": 0.5``

Software-Probleme
-----------------

**HRNGGUI startet nicht:**

.. code-block:: bash

   # Abhängigkeiten prüfen
   pip install --upgrade -r requirements.txt
   
   # Konfiguration zurücksetzen
   rm config.json

**GUI reagiert nicht:**
- Große Datenmengen → Puffergröße reduzieren
- Threading-Probleme → Neustart
- Memory-Leak → Task Manager prüfen

**Falsche Statistiken:**
- Mindest-Sampling-Zeit abwarten (30+ Sekunden)
- Chi-Quadrat nur bei >100 Datenpunkten aussagekräftig
- Outlier können Statistiken verzerren

Debug-Informationen
-------------------

**Detaillierte Logs aktivieren:**

.. code-block:: bash

   python main.py --debug --log-level DEBUG

**Logdateien finden:**
- Windows: ``%APPDATA%/HRNGGUI/logs/``
- Linux/Mac: ``~/.hrnggui/logs/``

**Wichtige Log-Nachrichten:**
- ``Serial connection established`` → Verbindung OK
- ``Data parsing error`` → Protokoll-Problem
- ``Buffer overflow`` → Performance-Problem

**Bug-Report erstellen:**
1. Debug-Logs sammeln
2. config.json anonymisieren  
3. Schritte zur Reproduktion dokumentieren
4. GitHub Issue erstellen

Performance-Tuning
------------------

**Für schwache Hardware:**

.. code-block:: json

   {
     "analysis": {
       "update_rate": 0.2,
       "histogram_bins": 20,
       "statistical_window": 500
     }
   }

**Für hohe Datenraten:**

.. code-block:: json

   {
     "acquisition": {
       "buffer_size": 100000,
       "batch_processing": true
     }
   }

Letzte Hilfe
------------

1. **Neuinstallation:** Repository neu klonen
2. **Factory Reset:** Alle Konfigurationsdateien löschen
3. **System-Reboot:** Treiber-Probleme beheben
4. **Community-Support:** GitHub Discussions verwenden
* Prüfen Sie die Kabelverbindung

Anwendungsprobleme
------------------

Anwendung startet nicht
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

Debug-Modus aktivieren
======================
python main.py --debug


Keine Daten empfangen
~~~~~~~~~~~~~~~~~~~~~

1. Prüfen Sie die Geräteeinstellungen
2. Testen Sie im Demo-Modus
3. Überprüfen Sie die Protokoll-Konfiguration

Logs und Debugging
------------------

Log-Dateien finden Sie unter:

* **Windows**: ``%APPDATA%\HRNGGUI\logs\``
* **macOS**: ``~/Library/Application Support/HRNGGUI/logs/``
* **Linux**: ``~/.config/HRNGGUI/logs/``
