# FAQ

Häufig gestellte Fragen zu HRNGGUI.

## Allgemeine Fragen

### Was ist HRNGGUI?

HRNGGUI ist eine grafische Benutzeroberfläche für die Steuerung und Datenerfassung von Geiger-Müller-Zählern zur Hardware-Zufallszahlengenerierung.

### Welche Geräte werden unterstützt?

- Arduino-basierte GM-Zähler
- Frederiksen Scientific GM-Zähler
- Kompatible Geräte mit serieller Schnittstelle

### Ist HRNGGUI kostenlos?

Ja, HRNGGUI ist Open Source und unter der MIT-Lizenz verfügbar.

## Technische Fragen

### Welche Python-Version wird benötigt?

Python 3.10 oder höher wird empfohlen.

### Kann ich HRNGGUI ohne Hardware testen?

Ja, verwenden Sie den Demo-Modus:

```bash
python main.py --demo
```

### Wie kann ich eigene Datenexporte erstellen?

HRNGGUI unterstützt CSV-Export. Für andere Formate können Sie die API verwenden.

## Probleme und Lösungen

### "Gerät nicht gefunden"

- Prüfen Sie die USB-Verbindung
- Installieren Sie die entsprechenden Treiber
- Überprüfen Sie die Berechtigungen

### "Import-Fehler"

- Installieren Sie alle Abhängigkeiten: `pip install -r requirements.txt`
- Verwenden Sie eine virtuelle Umgebung

### Weitere Fragen?

Öffnen Sie ein Issue auf [GitHub](https://github.com/cckssr/HRNGGUI/issues).
