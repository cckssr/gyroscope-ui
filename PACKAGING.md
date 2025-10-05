# Gyroscope UI - GitHub Package Konfiguration

Dieses Projekt ist als pip-Paket konfiguriert und kann direkt von GitHub installiert werden.

## 📦 Paket-Struktur

Das Paket enthält nur die notwendigen Dateien:

- `src/` → Python-Source-Code (als `gyroscope_ui` Paket)
- `pyqt/` → Qt UI-Definitionen (als `gyroscope_ui.pyqt` Subpaket)
- `config.json` → Konfigurationsdatei
- `README.md`, `LICENSE` → Dokumentation

**Ausgeschlossen** sind:

- `Arduino-Gyroscope/` → Hardware-Code
- `logs/`, `tests/`, `docs/` → Entwicklungs- und Testdateien
- `.ipynb` Notebooks und andere Entwicklungsdateien

## 🚀 Automatische Releases

Die GitHub Action `.github/workflows/release.yml` erstellt automatisch Releases:

### Workflow-Ablauf:

1. **Build**: Erstellt das Paket (.whl und .tar.gz)
2. **Test**: Testet die Installation auf Ubuntu, macOS und Windows mit Python 3.9-3.12
3. **Release**: Erstellt automatisch einen GitHub Release beim Push auf `main`
   - Liest Version aus `pyproject.toml`
   - Erstellt automatisch Git-Tag `vX.Y.Z`
   - Generiert Changelog aus Git-Commits
   - Lädt Build-Artefakte hoch

### Manueller Release:

Um einen Release zu erstellen:

1. Erhöhen Sie die Version in `pyproject.toml`:

   ```toml
   version = "1.0.1"  # oder die neue Version
   ```

2. Committen und pushen Sie auf `main`:

   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 1.0.1"
   git push origin main
   ```

3. Die GitHub Action wird automatisch ausgelöst und erstellt:
   - Ein Git-Tag `v1.0.1`
   - Einen GitHub Release mit Changelog
   - Build-Artefakte (.whl und .tar.gz Dateien)

### Installation nach Release:

Benutzer können dann installieren mit:

```bash
# Neueste Version
pip install git+https://github.com/cckssr/gyroscope-ui.git

# Spezifische Version
pip install git+https://github.com/cckssr/gyroscope-ui.git@v1.0.1

# Oder von heruntergeladenem Wheel
pip install gyroscope_ui-1.0.1-py3-none-any.whl
```

## 🔧 Lokale Entwicklung

Für die Entwicklung:

```bash
# Editierbare Installation
pip install -e .

# Mit Development-Tools
pip install -e ".[dev]"

# Paket lokal bauen
python -m build

# Paket testen
twine check dist/*
```

## 📝 PyPI-Veröffentlichung (optional)

Die Action enthält auch einen Job für PyPI-Veröffentlichung, der standardmäßig deaktiviert ist.

Um PyPI-Publishing zu aktivieren:

1. Erstellen Sie einen PyPI API Token
2. Fügen Sie ihn als GitHub Secret `PYPI_API_TOKEN` hinzu
3. Setzen Sie die GitHub Variable `ENABLE_PYPI_PUBLISH` auf `true`

## 🛠️ Wichtige Dateien

- `pyproject.toml` → Haupt-Konfiguration (Version, Dependencies, Entry Point)
- `MANIFEST.in` → Definiert, welche Dateien ins Paket kommen
- `.gitignore` → Ignoriert Build-Artefakte
- `.github/workflows/release.yml` → Automatische Release-Pipeline
- `setup.py` → Backwards-Compatibility für ältere pip-Versionen

## 📚 Entry Points

Das Paket installiert das Kommandozeilen-Tool `gyroscope-ui`:

```bash
# Nach Installation:
gyroscope-ui
```

Oder in Python:

```python
from gyroscope_ui.main import main
main()
```

## ⚙️ Konfiguration anpassen

Um die Paket-Konfiguration anzupassen, bearbeiten Sie `pyproject.toml`:

- **Version ändern**: `project.version`
- **Dependencies hinzufügen**: `project.dependencies`
- **Metadaten**: `project.name`, `project.description`, etc.
- **URLs aktualisieren**: `project.urls`
