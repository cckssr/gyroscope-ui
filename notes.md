Aus der Dänischen Anleitung:

## Datenstrom
Das automatische Streaming sendet Daten als Text mit 9600 Bits pro Sekunde. Standardmäßig wird ein Komma zwischen den Werten eingefügt:
    aktuelle Zählnummer,
    letztes abgeschlossenes Ergebnis,
    Zählzeit,
    Wiederholung (0/1),
    Fortschritt,
    Spannung
„Fortschritt“ bedeutet hier: Prozentsatz der gewählten Zählzeit. - Oder (bei unendlicher Zählzeit): Verstrichene Zeit in Sekunden.

## Kommunikationsprotokoll
Die Befehle an das Gerät bestehen aus einem Buchstaben, eventuell gefolgt von einer Zahl. Die möglichen Antworten des Gerätes hängen von dem Befehl ab.

## Streaming-Steuerung
Bei alleiniger Verwendung gibt der Befehl den Status zurück.
Wenn er mit einem Parameter 0-8 verwendet wird, ändert sich ändert sich die Funktion wie folgt:
    'b0' : Streaming stoppen  
    'b1' : Streaming-Daten senden, wenn die Messung bereit ist  
    'b2' : Streaming-Daten jetzt senden  
    'b3' : Jetzt senden und fortfahren, wenn bereit (b2+b1)  
    'b4' : Daten alle 50 ms senden  
    'b5' : Komma zwischen den Werten verwenden  
    'b6' : Semikolon zwischen den Werten verwenden  
    'b7' : Leerzeichen zwischen den Werten verwenden  
    'b8' : Tabulator zwischen den Werten verwenden  
(Standard ist b4 und b5. Wenn beim Einschalten des Geräts Start/Stop gedrückt und gehalten wird, entspricht dies b0).  

## Unternehmensinformationen
Rückgabe der Unternehmeninformation als Zeichenkette
    'c' : "(c) copyright 2020 Frederiksen Scientific A/S"

## Registerwerte lesen
Rückgabe des aktuellen Wertes aus dem Sekundärregister und Primärregister.
    'd' : Rückgabe Registerwert

## Ergebnisse senden oder nicht
Wenn der Befehl allein verwendet wird, wird der Status zurückgegeben.
Wenn der Befehl mit den Parametern 0-1 verwendet wird, ändert sich der Status wie folgt:
    'e0' Zählnummern werden nicht automatisch gesendet
    'e1' Zählnummern werden automatisch gesendet, wenn jede Zählperiode abgeschlossen ist.

## Zeit zählen
Bei alleiniger Verwendung gibt der Befehl die aktuelle Zählzeit in Sekunden wird zurückgegeben. Wenn der Befehl mit den Parametern 0-5 verwendet wird, ändert sich die Zählzeit in im Verhältnis zum Parameter:
    'f0' : Unendlich
    'f1' : 1s
    'f2' : 10s
    'f3' : 60s
    'f4' : 100s
    'f5' : 300s
Andere Zählzeiten sind ungültig. Die Anzeigesymbole werden in Abhängigkeit von der Zählzeit aktiviert.

## GM-Spannung
Bei alleiniger Verwendung gibt der Befehl die aktuelle GM-Spannung in Volt zurück. Wenn der Befehl mit den Parametern 400-700 verwendet wird, wird die GM-Spannung Spannung in Abhängigkeit vom Parameter geändert.
Beispiel:
    'j520' : GM-Spannung wird auf 520V gesetzt

## Einzel-/Wiederholungsmodus
Wenn der Befehl allein verwendet wird, wird der Status zurückgegeben.
Bei Verwendung des Befehls mit den Parametern 0-1,
ändert sich der Modus wie folgt:
    'o0' : Einzeln
    'o1' : Wiederholung

## Start/Stopp der Zählung.
Wenn der Befehl allein verwendet wird, gibt er den Status
ob eine Zählung im Gange ist. 0 bedeutet, dass eine Zählung nicht aktiv ist. Wenn er mit einer Zahl verwendet wird, kann eine Zählung gestartet oder gestoppt werden:
    's0' : Stoppt die Zählung (keine Funktion, wenn Zählung gestoppt ist)
    's1' : Startet die Zählung (keine Funktion, wenn die Zählung im Gange ist)

## Lautsprecher ein/aus
Wenn der Befehl allein verwendet wird, gibt er den aktuellen Status des Lautsprechers zurück. Wird der Befehl mit einer Nummer verwendet, wird der Lautsprecher entsprechend der Nummer ein-/ausgeschaltet:
    'U0' : GM-Ton aus - Bereitschaftston aus
    'U1' : GM-Ton an - Bereitschaftston aus
    'U2' : GM-Ton aus - Bereitschaftston ein
    'U3' : GM-Ton ein - Bereitschaftston ein

## Versionsnummer wird zurückgegeben
    'v' : GM-Zähler. Firmware-Version xxxxxxxx'

## Lesen der fertigen Zählnummern
Register, in das der Wert aus dem Primärregister nach Ende der Zählzeit kopiert wird. Das Register wird gelöscht, wenn es gelesen wird. Wenn das Register abgefragt wird und es ist leer ist - wird „-1“ zurückgegeben
Um sicherzustellen, dass alle Werte an den PC übertragen werden muss dieses Register mit einer Frequenz gelesen werden, die (etwas) höher ist höher ist als die Zählzeitfrequenz.
    'w' : Zählerregister lesen
