# 🚀 Quick Start Guide - Paket-Distribution

## Für Entwickler: Release erstellen

### 1. Version erhöhen

Bearbeiten Sie `pyproject.toml`:

```toml
[project]
name = "gyroscope-ui"
version = "1.0.1"  # ← Hier die neue Version eintragen
```

### 2. Änderungen committen und pushen

```bash
git add pyproject.toml
git commit -m "Bump version to 1.0.1"
git push origin main
```

### 3. Fertig! 🎉

Die GitHub Action erstellt automatisch:

- ✅ Git-Tag `v1.0.1`
- ✅ GitHub Release mit Changelog
- ✅ Downloadbare `.whl` und `.tar.gz` Dateien

## Für Entwickler: Lokal testen

```bash
# Paket-Konfiguration validieren
python validate_package.py

# Oder manuell:
python -m pip install --upgrade build twine
python -m build
twine check dist/*
```

## Für Benutzer: Installation

### Von GitHub (neueste Version)

```bash
pip install git+https://github.com/cckssr/gyroscope-ui.git
```

### Spezifische Version

```bash
pip install git+https://github.com/cckssr/gyroscope-ui.git@v1.0.0
```

### Von heruntergeladenem Wheel

```bash
pip install gyroscope_ui-1.0.0-py3-none-any.whl
```

### Starten

```bash
gyroscope-ui
```

Oder in Python:

```python
from gyroscope_ui.main import main
main()
```

## 📁 Was ist im Paket enthalten?

✅ **Enthalten:**

- `src/` → Python-Source als `gyroscope_ui` Paket
- `pyqt/` → UI-Definitionen als `gyroscope_ui.pyqt`
- `config.json` → Konfiguration
- `README.md`, `LICENSE`

❌ **Nicht enthalten:**

- `Arduino-Gyroscope/` (Hardware-Code)
- `logs/`, `tests/`, `docs/` (Entwicklung)
- `.ipynb` (Notebooks)

## 🔧 Entwicklungs-Setup

```bash
# Repository klonen
git clone https://github.com/cckssr/gyroscope-ui.git
cd gyroscope-ui

# Editierbare Installation
pip install -e .

# Mit Dev-Tools
pip install -e ".[dev]"
```

## 📚 Weitere Dokumentation

- [INSTALL.md](INSTALL.md) - Detaillierte Installationsanleitung
- [PACKAGING.md](PACKAGING.md) - Paket-System-Dokumentation
- [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) - Übersicht aller Änderungen

## ⚙️ GitHub Action Konfiguration

Die Action läuft automatisch bei:

- ✅ Push auf `main` Branch
- ✅ Manueller Trigger über "Actions" Tab

Workflow-Dateien:

- `.github/workflows/release.yml` - Automatische Releases
- `.github/workflows/test-build.yml` - Test-Builds für PRs

## 🐛 Troubleshooting

### "Module gyroscope_ui not found"

→ Installieren Sie das Paket: `pip install -e .`

### "Permission denied" beim Push

→ Prüfen Sie GitHub Permissions in Settings > Actions

### Build schlägt fehl

→ Führen Sie `python validate_package.py` aus

### GitHub Action läuft nicht

→ Prüfen Sie den Actions-Tab auf GitHub

### Windows: "Invalid wheel filename (wrong number of parts): '\*'"

→ Dieser Fehler wurde behoben! Verwenden Sie die neue Version vom main Branch.
→ Details siehe [BUGFIXES.md](BUGFIXES.md)

## 💡 Tipps

1. **Semantic Versioning**: Verwenden Sie `MAJOR.MINOR.PATCH`

   - MAJOR: Breaking Changes
   - MINOR: Neue Features (backwards compatible)
   - PATCH: Bug Fixes

2. **Commits**: Verwenden Sie aussagekräftige Commit-Messages

   - Die GitHub Action generiert daraus den Changelog

3. **Testing**: Testen Sie lokal vor dem Push

   - `python validate_package.py`
   - `pip install dist/*.whl`

4. **Documentation**: Aktualisieren Sie README.md bei größeren Änderungen
