# Installation

Diese Anleitung führt Sie durch die Installation der HRNGGUI-Anwendung.

## Systemanforderungen

### Mindestanforderungen

- **Betriebssystem**: Windows 10+, macOS 10.15+, oder Linux (Ubuntu 20.04+)
- **Python**: Version 3.10 oder höher
- **RAM**: 4 GB (8 GB empfohlen)
- **Speicherplatz**: 500 MB freier Speicherplatz
- **Hardware**: USB-Port für GM-Zähler-Verbindung

### Empfohlene Ausstattung

- **Python**: Version 3.11 oder 3.12
- **RAM**: 8 GB oder mehr
- **Speicherplatz**: 1 GB für Daten und Logs
- **Display**: 1920x1080 oder höher

## Installation

### Option 1: Pip-Installation (Empfohlen)

```bash
# Virtuelle Umgebung erstellen (empfohlen)
python -m venv hrnggui-env

# Virtuelle Umgebung aktivieren
# Windows:
hrnggui-env\Scripts\activate
# macOS/Linux:
source hrnggui-env/bin/activate

# HRNGGUI installieren
pip install hrnggui
```

### Option 2: Quellcode-Installation

```bash
# Repository klonen
git clone https://github.com/cckssr/HRNGGUI.git
cd HRNGGUI

# Abhängigkeiten installieren
pip install -r requirements.txt

# Anwendung starten
python main.py
```

### Option 3: Download-Installation

1. Laden Sie die neueste Version von der [Releases-Seite](https://github.com/cckssr/HRNGGUI/releases) herunter
2. Entpacken Sie das Archiv
3. Installieren Sie die Abhängigkeiten:

```bash
pip install -r requirements.txt
```

## Abhängigkeiten

Die folgenden Python-Pakete werden benötigt:

```text
PySide6>=6.5.0
matplotlib>=3.7.0
numpy>=1.24.0
pyserial>=3.5
```

### Vollständige Abhängigkeitsliste

```bash
# Anzeigen aller installierten Abhängigkeiten
pip list
```

## Erste Einrichtung

### 1. Konfiguration erstellen

Beim ersten Start wird automatisch eine Konfigurationsdatei erstellt:

```json
{
  "debug_level": 1,
  "auto_connect": false,
  "default_port": "",
  "theme": "light",
  "language": "de"
}
```

### 2. Gerätetreiber installieren

#### Windows

1. Laden Sie die Arduino-Treiber von der [offiziellen Website](https://www.arduino.cc/en/software) herunter
2. Installieren Sie die Treiber
3. Starten Sie den Computer neu

#### macOS

Keine zusätzlichen Treiber erforderlich. macOS erkennt Arduino-Geräte automatisch.

#### Linux

```bash
# Benutzer zur dialout-Gruppe hinzufügen
sudo usermod -a -G dialout $USER

# Abmelden und wieder anmelden
logout
```

### 3. Geräteverbindung testen

1. Schließen Sie Ihren GM-Zähler an
2. Starten Sie HRNGGUI
3. Gehen Sie zu "Gerät" → "Verbinden"
4. Wählen Sie den entsprechenden Port aus

## Fehlerbehebung

### Häufige Probleme

#### "Kein Modul namens 'PySide6' gefunden"

```bash
# PySide6 installieren
pip install PySide6
```

#### "Port nicht gefunden" oder "Zugriff verweigert"

**Windows:**

- Überprüfen Sie den Geräte-Manager
- Installieren Sie die Arduino-Treiber neu

**macOS:**

- Überprüfen Sie die Systemeinstellungen → Sicherheit
- Erlauben Sie den Zugriff auf USB-Geräte

**Linux:**

```bash
# Benutzerrechte überprüfen
groups $USER

# Sollte "dialout" enthalten
sudo usermod -a -G dialout $USER
```

#### "Matplotlib-Backend-Fehler"

```bash
# Zusätzliche Abhängigkeiten installieren
# Ubuntu/Debian:
sudo apt-get install python3-tk

# macOS:
brew install python-tk

# Windows: Meist nicht erforderlich
```

### Debug-Modus aktivieren

Für detaillierte Fehlersuche:

```bash
# Umgebungsvariable setzen
export HRNGGUI_DEBUG=1

# Oder in der Konfigurationsdatei
{
    "debug_level": 3
}
```

## Deinstallation

### Pip-Installation

```bash
pip uninstall hrnggui
```

### Quellcode-Installation

```bash
# Verzeichnis löschen
rm -rf HRNGGUI

# Virtuelle Umgebung entfernen
rm -rf hrnggui-env
```

### Konfigurationsdateien entfernen

```bash
# Windows:
del /q "%APPDATA%\HRNGGUI\*"

# macOS:
rm -rf ~/Library/Application\ Support/HRNGGUI

# Linux:
rm -rf ~/.config/HRNGGUI
```

## Aktualisierung

### Pip-Installation

```bash
pip install --upgrade hrnggui
```

### Quellcode-Installation

```bash
cd HRNGGUI
git pull origin main
pip install -r requirements.txt
```

## Verifizierung

Nach der Installation können Sie die Funktionalität testen:

```bash
# Version anzeigen
python -c "import hrnggui; print(hrnggui.__version__)"

# Testlauf im Demo-Modus
python main.py --demo
```

## Unterstützung

Bei Installationsproblemen:

- Konsultieren Sie die [Fehlerbehebung](troubleshooting.md)
- Öffnen Sie ein [Issue auf GitHub](https://github.com/cckssr/HRNGGUI/issues)
- Prüfen Sie die [FAQ](faq.md)

## Nächste Schritte

Nach erfolgreicher Installation:

1. Lesen Sie den [Schnellstart-Guide](quickstart.md)
2. Konfigurieren Sie die [Grundeinstellungen](configuration.md)
3. Verbinden Sie Ihr [Gerät](device-connection.md)
