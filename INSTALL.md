# Installationsanleitung

## Installation des Pakets

### Von GitHub (empfohlen)

Sie können das Paket direkt von GitHub installieren:

```bash
# Neueste Version vom main branch
pip install git+https://github.com/cckssr/gyroscope-ui.git

# Spezifische Version (z.B. v1.0.0)
pip install git+https://github.com/cckssr/gyroscope-ui.git@v1.0.0
```

### Von einer lokalen Kopie

Wenn Sie das Repository geklont haben:

```bash
cd gyroscope-ui
pip install .

# Für Entwicklung (editierbare Installation)
pip install -e .
```

### Von einem Release-Wheel

Laden Sie die `.whl`-Datei von den GitHub Releases herunter und installieren Sie:

```bash
pip install gyroscope_ui-1.0.0-py3-none-any.whl
```

## Verwendung

Nach der Installation können Sie die GUI über die Kommandozeile starten:

```bash
gyroscope-ui
```

Oder in Python importieren:

```python
from gyroscope_ui.main import main
main()
```

## Entwicklung

Für die Entwicklung installieren Sie das Paket im editierbaren Modus mit Dev-Abhängigkeiten:

```bash
pip install -e ".[dev]"
```

## Deinstallation

```bash
pip uninstall gyroscope-ui
```
