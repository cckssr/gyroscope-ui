# HRNGGUI Testplan

Dieser Testplan dient zur systematischen Überprüfung der HRNGGUI-Anwendung nach Änderungen. Er deckt die wichtigsten Funktionen ab und stellt sicher, dass die Kernfunktionalität nach dem Refactoring weiterhin korrekt funktioniert.

## 1. Initialisierung und grundlegende UI-Funktionen

- [ ] Die Anwendung startet ohne Fehler
- [ ] Alle UI-Elemente werden korrekt angezeigt
- [ ] Der Plot-Bereich wird korrekt initialisiert
- [ ] Die Statusleiste zeigt die korrekte Startmeldung an

## 2. Geräteverbindung

- [ ] Die Anwendung erkennt verfügbare serielle Ports
- [ ] Verbindung mit einem ausgewählten Port kann hergestellt werden
- [ ] Die Verbindungsstatus-Anzeige aktualisiert sich korrekt
- [ ] Fehlermeldungen bei nicht erfolgreicher Verbindung werden angezeigt

## 3. Messungen

- [ ] Messung kann gestartet werden
- [ ] Daten werden während der Messung empfangen und angezeigt
- [ ] Messwerte werden im Plot korrekt dargestellt
- [ ] Messung kann gestoppt werden
- [ ] Wiederholungsmodus funktioniert korrekt
- [ ] Abfragemodus (Automatisch/Manuell) funktioniert korrekt

## 4. Datenverarbeitung

- [ ] Erfasste Messwerte werden korrekt gespeichert
- [ ] Der Verlauf wird korrekt angezeigt
- [ ] Statistiken werden korrekt berechnet
- [ ] Daten können in CSV-Datei exportiert werden
- [ ] Daten können zurückgesetzt werden

## 5. GM-Zähler-Steuerung

- [ ] Spannungseinstellung funktioniert korrekt
- [ ] Messmodus (Einzel/Wiederholung) kann geändert werden
- [ ] Abfrageintervall kann geändert werden
- [ ] Messdauer kann geändert werden
- [ ] Änderungen werden an das Gerät übertragen

## 6. Fehlerbehandlung

- [ ] Verbindungsverlust wird erkannt und gemeldet
- [ ] Fehlerhafte Eingaben werden abgefangen
- [ ] Bei ungültigen Daten vom Gerät werden entsprechende Fehlermeldungen angezeigt
- [ ] Nach einem Fehler kann die Anwendung weiter verwendet werden

## 7. Speichern und Laden

- [ ] Messdaten können als CSV gespeichert werden
- [ ] Die gespeicherten Daten enthalten alle erforderlichen Informationen
- [ ] Beim Starten einer neuen Messung mit ungespeicherten Daten wird nachgefragt

## 8. Leistung

- [ ] Die Anwendung reagiert auch bei längeren Messungen flüssig
- [ ] Der Speicherverbrauch steigt nicht unverhältnismäßig an
- [ ] Die Plot-Aktualisierung erfolgt performant auch bei vielen Datenpunkten

## Testumgebung

- **Betriebssystem:**
- **Python-Version:**
- **Getestete Hardware:**
- **Datum des Tests:**
- **Tester:**

## Ergebnisse

- **Status:** (Bestanden/Teilweise bestanden/Nicht bestanden)
- **Kritische Fehler:**
- **Nicht kritische Fehler:**
- **Weitere Bemerkungen:**
