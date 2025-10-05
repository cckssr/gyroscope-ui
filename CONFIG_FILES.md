# config.json Dateien - Erklärung

## Es gibt ZWEI config.json Dateien:

### 1. `/config.json` (Root)

**Zweck:** Nur für lokale Entwicklung

- ✅ Wird von Git getrackt
- ❌ **NICHT** im pip-Paket enthalten
- 📝 Für Entwickler die `python main.py` direkt ausführen

### 2. `/src/config.json` (Package)

**Zweck:** Im installierten Paket

- ✅ Wird von Git getrackt
- ✅ **IM** pip-Paket enthalten
- 📦 Für installierte Benutzer

## Wie funktioniert das Laden?

Die Funktion `import_config()` in `src/helper_classes.py` prüft mehrere Pfade:

```python
config_locations = [
    Path("config.json"),                           # 1. CWD (Entwicklung)
    Path(__file__).parent / "config.json",         # 2. Package dir (installiert)
    Path(__file__).parent.parent / "config.json",  # 3. Root (Entwicklung fallback)
]
```

## Szenarien:

### Szenario 1: Lokale Entwicklung

```bash
python main.py
```

→ Findet `config.json` im CWD (Root) ✅

### Szenario 2: Installiertes Paket

```bash
pip install git+https://github.com/cckssr/gyroscope-ui.git
gyroscope-ui
```

→ Findet `src/config.json` (im Package) ✅

### Szenario 3: Editable Install

```bash
pip install -e .
gyroscope-ui
```

→ Findet beide, nutzt die erste gefundene ✅

## Wartung:

**Wichtig:** Beide Dateien müssen synchron bleiben!

Wenn Sie Änderungen an der Konfiguration vornehmen:

```bash
# Änderungen in einer Datei machen, dann:
cp config.json src/config.json
```

Oder Script nutzen:

```bash
# Einmalig ausführbar machen
chmod +x scripts/sync-config.sh

# Dann immer wenn config.json geändert wird
./scripts/sync-config.sh
```

## Warum nicht nur eine Datei?

**Option A:** Nur `src/config.json`

- ❌ Entwickler müssen imports von `src.` verwenden
- ❌ Komplizierter für lokale Entwicklung

**Option B:** Nur Root `config.json`

- ❌ Nicht im Paket enthalten
- ❌ Installierte Benutzer haben keine Config

**Option C:** Beide (aktuell) ✅

- ✅ Funktioniert in allen Szenarien
- ✅ Einfach für Entwicklung
- ✅ Komplett für Paket
- ⚠️ Muss synchron gehalten werden

## Alternative: Symlink (nur Unix/macOS)

Für Entwickler auf Unix-Systemen:

```bash
rm src/config.json
ln -s ../config.json src/config.json
```

⚠️ Funktioniert NICHT für:

- Windows (ohne Dev-Mode)
- Git (Symlinks werden nicht ideal gehandhabt)
- Distribution (Symlinks werden zu echten Dateien)
