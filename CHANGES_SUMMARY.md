# Änderungen für pip-Paket-Konfiguration

## ✅ Durchgeführte Änderungen

### 1. **pyproject.toml** aktualisiert

- Paketname von `GYRO-UI` zu `gyroscope-ui` geändert (pip-konform)
- Lizenz auf Apache-2.0 aktualisiert
- Entry Point `gyroscope-ui` hinzugefügt → CLI-Command nach Installation
- Package-Struktur konfiguriert:
  - `src/` → `gyroscope_ui` Paket
  - `pyqt/` → `gyroscope_ui.pyqt` Subpaket
- Package-Data für `.json` und `.ui` Dateien konfiguriert
- Repository-URLs auf `cckssr/gyroscope-ui` aktualisiert

### 2. **MANIFEST.in** erstellt

- Definiert, welche Dateien ins Paket eingeschlossen werden:
  - ✅ README.md, LICENSE, requirements.txt, config.json
  - ✅ pyqt/\*.ui Dateien
- Ausschlüsse:
  - ❌ Arduino-Gyroscope/
  - ❌ logs/, tests/, docs/, scripts/, static/
  - ❌ .ipynb, .pyproject.user Dateien

### 3. **GitHub Actions** erstellt

#### `.github/workflows/release.yml`

Automatische Release-Pipeline mit:

- **Build**: Erstellt wheel (.whl) und source (.tar.gz)
- **Test**: Multi-Platform-Tests (Ubuntu, macOS, Windows) mit Python 3.9-3.12
- **Release**: Automatische Releases beim Push auf `main`
  - Liest Version aus pyproject.toml
  - Erstellt Git-Tag (z.B. `v1.0.0`)
  - Generiert Changelog aus Git-Commits
  - Erstellt GitHub Release mit Installationsanweisungen
  - Lädt Build-Artefakte hoch
- **PyPI**: Optional (deaktiviert, kann aktiviert werden)

#### `.github/workflows/test-build.yml`

Test-Pipeline für Pull Requests

### 4. **main.py** angepasst

- Imports unterstützen jetzt beide Modi:
  - Als installiertes Paket: `from gyroscope_ui.xxx import ...`
  - Aus Quellcode: `from src.xxx import ...`
- Fallback-Mechanismus für Kompatibilität

### 5. **setup.py** erstellt

- Backwards-Compatibility für ältere pip-Versionen
- Leitet zu pyproject.toml weiter

### 6. **.gitignore** erweitert

- Build-Artefakte: dist/, build/, _.egg-info/, _.whl
- Python-Bytecode: _.pyc, _.pyo

### 7. **Dokumentation** erstellt

#### INSTALL.md

- Detaillierte Installationsanweisungen
- Installation von GitHub
- Installation von Wheel-Files
- Entwicklungs-Setup

#### PACKAGING.md

- Komplette Dokumentation des Paket-Systems
- Release-Prozess erklärt
- Konfigurationsoptionen
- Entwickler-Guide

#### README.md aktualisiert

- Neue Installationsanweisungen
- Links zur Dokumentation

## 🚀 Verwendung

### Für Endbenutzer

Nach dem Push auf `main` mit neuer Version:

```bash
pip install git+https://github.com/cckssr/gyroscope-ui.git
gyroscope-ui
```

### Für Entwickler

```bash
git clone https://github.com/cckssr/gyroscope-ui.git
cd gyroscope-ui
pip install -e ".[dev]"
```

### Release erstellen

1. Version in `pyproject.toml` erhöhen:

   ```toml
   version = "1.0.1"
   ```

2. Committen und pushen:

   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 1.0.1"
   git push origin main
   ```

3. GitHub Action erstellt automatisch:
   - Git-Tag `v1.0.1`
   - GitHub Release
   - Build-Artefakte

## 📦 Paket-Inhalt

Das installierte Paket enthält NUR:

```
gyroscope_ui/
├── __init__.py
├── connection.py
├── data_controller.py
├── debug_utils.py
├── device_manager.py
├── helper_classes.py
├── main.py
├── main_window.py
├── plot.py
├── config.json
└── pyqt/
    ├── __init__.py
    └── *.ui
```

Nicht enthalten: Arduino-Code, Tests, Logs, Docs, Notebooks

## ⚙️ Nächste Schritte

1. **Ersten Release erstellen**:

   ```bash
   git add .
   git commit -m "Configure package distribution and GitHub Actions"
   git push origin main
   ```

2. **PyPI aktivieren** (optional):

   - PyPI-Account erstellen
   - API-Token erstellen
   - Als GitHub Secret `PYPI_API_TOKEN` hinzufügen
   - GitHub Variable `ENABLE_PYPI_PUBLISH=true` setzen

3. **Testen**:
   - Nach dem Push prüfen ob GitHub Action läuft
   - Release in GitHub überprüfen
   - Installation testen: `pip install git+https://github.com/cckssr/gyroscope-ui.git`

## 🔍 Verifizierung

Lokal testen vor dem Push:

```bash
# Paket bauen
python -m pip install --upgrade build twine
python -m build

# Paket prüfen
twine check dist/*

# Installation testen
pip install dist/*.whl
gyroscope-ui
```
