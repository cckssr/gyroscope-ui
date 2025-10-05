# 📝 Update: config.json Dateien

## ❓ Frage: Ist die alte config.json überflüssig?

**Kurze Antwort:** Nein, aber sie wird **nicht** im pip-Paket enthalten sein.

## 📂 Die zwei config.json Dateien:

### `/config.json` (Root)

- **Zweck:** Für lokale Entwicklung
- **Im Git:** ✅ Ja
- **Im Paket:** ❌ Nein
- **Verwendet von:** Entwickler, die `python main.py` ausführen

### `/src/config.json` (Package)

- **Zweck:** Im installierten pip-Paket
- **Im Git:** ✅ Ja
- **Im Paket:** ✅ Ja
- **Verwendet von:** Installierte Benutzer via `pip install`

## 🔄 Warum beide behalten?

Die `import_config()` Funktion prüft **mehrere Pfade**:

1. Current Working Directory → für Entwicklung
2. Package Directory → für installiertes Paket
3. Parent Directory → Fallback

Dies ermöglicht:

- ✅ Lokale Entwicklung: `python main.py` funktioniert
- ✅ Installiertes Paket: `gyroscope-ui` funktioniert
- ✅ Editable Install: `pip install -e .` funktioniert

## 🛠️ Wartung

**Wichtig:** Beide Dateien müssen synchron bleiben!

### Manuell:

```bash
cp config.json src/config.json
```

### Mit Script:

```bash
./scripts/sync-config.sh
```

## 📦 Was ist im Paket?

Das MANIFEST.in wurde aktualisiert:

```
# config.json im Root wird NICHT inkludiert
# Nur src/config.json ist im Paket (via pyproject.toml package-data)
```

## ✅ Änderungen vorgenommen:

1. ✅ MANIFEST.in aktualisiert - Root config.json nicht mehr explizit inkludiert
2. ✅ CONFIG_FILES.md erstellt - Ausführliche Dokumentation
3. ✅ scripts/sync-config.sh erstellt - Sync-Script

## 🎯 Fazit

**Beide Dateien haben ihren Zweck:**

- Root: Entwicklung
- src/: Distribution

**Im pip-Paket** ist nur `src/config.json` enthalten, was korrekt ist! ✅

Siehe [CONFIG_FILES.md](CONFIG_FILES.md) für Details.
