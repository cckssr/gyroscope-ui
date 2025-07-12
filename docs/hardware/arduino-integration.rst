Arduino Integration
===================

Anleitung zur Verwendung von Arduino-basierten GM-Zählern mit HRNGGUI.

Hardware-Setup
--------------

**Benötigte Komponenten:**
- Arduino Uno/Nano/Pro Mini
- GM-Röhre (z.B. SBM-20, J305βγ)
- Hochspannungsmodul (~400V)
- Pull-up Widerstand (10kΩ)
- USB-Kabel für Datenübertragung

**Verkabelung:**
- GM-Röhre Anode → HV+ (400V)
- GM-Röhre Kathode → Arduino Pin 2 (Interrupt) + 10kΩ Pull-up zu 5V
- HV- → Arduino GND

Arduino-Code
------------

Minimal-Code für HRNGGUI-Kompatibilität:

.. code-block:: cpp

   volatile unsigned long pulseCount = 0;
   unsigned long lastTime = 0;
   
   void setup() {
     Serial.begin(9600);
     pinMode(2, INPUT_PULLUP);
     attachInterrupt(digitalPinToInterrupt(2), countPulse, FALLING);
   }
   
   void loop() {
     unsigned long currentTime = millis();
     if (currentTime - lastTime >= 1000) {  // Jede Sekunde
       Serial.println(pulseCount);
       pulseCount = 0;
       lastTime = currentTime;
     }
   }
   
   void countPulse() {
     pulseCount++;
   }

**Erweiterte Version mit Zeitstempel:**

.. code-block:: cpp

   void loop() {
     if (pulseCount > 0) {
       unsigned long timestamp = millis();
       Serial.print(timestamp);
       Serial.print(",");
       Serial.println(pulseCount);
       pulseCount = 0;
     }
     delay(100);
   }

HRNGGUI-Konfiguration
--------------------

Für Arduino-Geräte in ``config.json``:

.. code-block:: json

   {
     "device": {
       "port": "auto",
       "baudrate": 9600,
       "timeout": 2.0,
       "protocol": "arduino"
     },
     "acquisition": {
       "expected_rate": 30,    // Erwartete counts/min
       "calibration_factor": 1.0
     }
   }

**Port-Erkennung (manuell):**
- Windows: ``COM3``, ``COM4``, etc.
- Linux: ``/dev/ttyUSB0``, ``/dev/ttyACM0``
- macOS: ``/dev/cu.usbmodem*``

Protokoll-Details
-----------------

**Standard-Format:**
- Ein Wert pro Zeile
- Dezimalzahl (Anzahl Pulse)
- Zeilenende: ``\n``

**Mit Zeitstempel:**
- Format: ``timestamp,count``
- Timestamp in Millisekunden
- Komma-separiert

**Fehlerbehandlung:**
- Ungültige Zeilen werden ignoriert
- Timeout führt zu Verbindungsabbruch
- Automatischer Reconnect verfügbar

Troubleshooting
---------------

**Keine Daten empfangen:**
- Serieller Monitor testen: ``screen /dev/ttyUSB0 9600``
- Baudrate überprüfen (9600 vs. 115200)
- Verkabelung und Spannungsversorgung prüfen

**Unrealistische Zählraten:**
- HV-Spannung anpassen (typisch 380-420V)
- Störquellen eliminieren (Handy, WLAN)
- Pull-up Widerstand überprüfen

**Verbindungsabbrüche:**
- USB-Kabel und -Port wechseln
- Timeout-Werte erhöhen
- Arduino-Reset vermeiden (DTR deaktivieren)

Optimierungen
-------------

**Performance:**
- Buffer-basierte Ausgabe für hohe Raten
- Interrupt-basiertes Counting (nicht Polling)
- Dedizierte Timer für präzise Zeitstempel

**Genauigkeit:**
- Deadtime-Korrektur implementieren
- Temperaturkompensation
- Kalibrierung mit bekannter Quelle
