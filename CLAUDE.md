# CLAUDE.md

PySide6 application for the "Kreisel" (gyroscope) experiment of the TU Berlin lab course (TK8).
Read `docs/CONCEPT.md` before working on anything; it is the specification. The wire protocol is
`docs/PROTOCOL.md`, the structure `docs/ARCHITECTURE.md`, the work plan `docs/MIGRATION_PLAN.md`.
Structure, conventions and UX follow `../spectrum-ui` (and `../oct-ui`); copy their generic
modules rather than reinventing them.

## Hardware

- Arduino Nano ESP32 per disc (10 units, `Kreisel-<DEVICE_ID>`), LSM6DS33 IMU + Hall sensor; firmware in `Arduino-Gyroscope/` (PlatformIO, C++, OTA via espota).
- Link: the board's own WiFi AP, UDP port 12345 at `192.168.4.1`, one ASCII CSV line per sample (≈ 100 Hz). No serial data path.
- Pure Python on the host; targets Windows (lab) and macOS (development).

## Architecture

```text
ui/ → infrastructure/ → core/        (ui/ may also import core/ directly)
```

- `gyroscope_ui/core/`: pure Python + NumPy. No Qt, no sockets, no file I/O. `models.py` is the contract between layers.
- `gyroscope_ui/infrastructure/`: UDP device adapter, mock, storage, session store, config, logging, paths. Qt only inside `infrastructure/qt_threads.py`.
- `gyroscope_ui/ui/`: controllers, tabs (registry), widgets, main window. Visual structure in Qt Designer `.ui` files under `gyroscope_ui/pyqt/` (generated `*_ui.py` via `pyqt/pyuic.sh`, never edited by hand).
- The CSV format of saved measurements is fixed (3 columns, byte-compatible with 1.1.x); extra information goes into the JSON sidecar.

## Conventions

- User-visible UI strings are **German** and live in `gyroscope_ui/config.json`; code, comments, docstrings, logs, tests and docs are English. Errors carry message keys, not texts.
- Units in names: `_s`, `_ms`, `_hz`, `_rad_s`, `_m_s2`.
- Type hints everywhere, `from __future__ import annotations`, ruff clean (`.venv/bin/ruff check .`, `.venv/bin/ruff format .`).
- Tests: core → unit tests, infrastructure → against the mock and the loopback fake firmware, ui → pytest-qt. Hardware is never required.
- The firmware keeps its own style; existing German comments stay, new code and comments are English.

## Environment

- venv: `.venv` (Python 3.14). Run tools as `.venv/bin/python`, `.venv/bin/pytest`, `.venv/bin/ruff`.
- Run the app: `.venv/bin/python -m gyroscope_ui --simulate`.
- Firmware: `cd Arduino-Gyroscope && pio run` (build), `pio run -e <ID> -t upload` (OTA).
