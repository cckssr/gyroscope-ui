FAQ
===

Häufige Fragen zur HRNGGUI-Nutzung.

Grundlagen
----------

**Was ist HRNGGUI?**
HRNGGUI erfasst und analysiert Daten von Geiger-Müller-Zählern für wissenschaftliche Zufallszahlengenerierung.

**Welche Hardware wird unterstützt?**
- Arduino-basierte GM-Zähler mit serieller Ausgabe
- Frederiksen Scientific Geräte  
- Selbstgebaute Zähler (115200 Baud, Standard-Protokoll)

**Funktioniert es ohne Hardware?**
Ja, Demo-Modus verfügbar: ``python main.py --demo``

**Welche Ausgabeformate gibt es?**
CSV (Standard), JSON (Metadaten), Binär (Rohdaten)

Technische Fragen
-----------------

**Warum zeigt die App "Keine Verbindung"?**
- COM-Port falsch oder belegt
- Baudrate prüfen (Standard: 115200)
- Treiber für USB-Seriell-Adapter installieren

**Datenerfassung funktioniert nicht?**
- Hardware-Protokoll in Einstellungen überprüfen
- Debug-Modus aktivieren für detaillierte Logs
- Timeout-Werte anpassen

**Wie interpretiere ich die statistischen Tests?**
- Chi-Quadrat p-Wert > 0.05 = gute Zufallsqualität
- Histogramm sollte gleichmäßig verteilt sein
- Lange Messperioden (>10 min) für aussagekräftige Ergebnisse

**Kann ich die Software erweitern?**
Ja, siehe :doc:`architecture` für API-Dokumentation und Entwicklerinfos.

**Performance-Probleme bei langen Messungen?**
- Puffergröße in Konfiguration reduzieren
- Automatischen Export aktivieren
- Diagramm-Update-Rate verringern

Support
-------

**Bug-Reports:** GitHub Issues verwenden
**Feature-Requests:** Pull Requests willkommen  
**Dokumentation:** Diese Seiten durchsuchen

"Gerät nicht gefunden"
~~~~~~~~~~~~~~~~~~~~~~

* Prüfen Sie die USB-Verbindung
* Installieren Sie die entsprechenden Treiber
* Überprüfen Sie die Berechtigungen

"Import-Fehler"
~~~~~~~~~~~~~~~

* Installieren Sie alle Abhängigkeiten: ``pip install -r requirements.txt``
* Verwenden Sie eine virtuelle Umgebung

Weitere Fragen?
~~~~~~~~~~~~~~~

Öffnen Sie ein Issue auf `GitHub <https://github.com/cckssr/HRNGGUI/issues>`_.
