# Kreisel-GUI

Kreisel-GUI is a PySide6 application for the "Kreisel" (gyroscope) experiment of the TU Berlin lab
course (TK8). A spinning disc carries an Arduino Nano ESP32 with an IMU and a Hall sensor. The
board streams the rotation frequency and the angular rates over its own WiFi. The application
shows the values live, records measurements and saves them as CSV files for the students'
evaluation.

The application runs on Windows (lab PCs) and macOS (development). The firmware for the boards is
in `Arduino-Gyroscope/`.

## Features

- **Device panel ("Gerät")** with a status LED (grey, amber, green, red), connect and
  disconnect, and a simulation switch. The connection recovers automatically when data return.
- **Live values ("Live-Messwerte")**: rotation frequency (Hz), angular rate about z ω_z (rad/s),
  number of recorded points and recording duration.
- **Plots ("Messung" tab)**: frequency and ω_z over time with linked axes, a rolling 30 s preview
  before recording, "Auto-Scroll" and "Auto-Range", and optional curves for all channels
  ("Alle Kanäle").
- **Measurement**: "Start", "Stop" and "Zurücksetzen" (reset). Unsaved data are never discarded
  without a question.
- **Saving**: "Speichern …" saves a measurement manually into the Dropbox-style folder of the lab.
  "Automatisch speichern" saves on Stop into group folders.
- **Files**: the CSV keeps the three columns of version 1.1.x, and a JSON sidecar with the metadata
  is written next to it.
- **Session**: group letter, sub-group and suffix are remembered for one day. The data folder,
  auto-save setting and window layout are restored on start.
- **Simulation mode**: `--simulate` runs the whole application without hardware.
- **Keyboard shortcuts**: for example `Space` for Start and Stop, `Ctrl+S` for saving. See
  [docs/SHORTCUTS.md](docs/SHORTCUTS.md).

## Hardware

- **Board**: Arduino Nano ESP32, one per disc (ten units, `Kreisel-E94464` and
  `Kreisel-E35433` to `Kreisel-E35441`).
- **IMU**: LSM6DS33 (accelerometer and gyroscope), read over SPI.
- **Hall sensor**: one magnet on the disc, so one pulse per revolution.
- **Link**: the board runs its own WiFi access point `Kreisel-<DEVICE_ID>`. The data are sent by UDP
  to port 12345 at `192.168.4.1`, one ASCII line per sample, about 80 to 100 samples per second.

The complete wire protocol is in [docs/PROTOCOL.md](docs/PROTOCOL.md).

**Known firmware quirk (version 1.1.1):** if the frequency changes by less than 0.05 Hz for 2 s, the
firmware reports 0 Hz until the next Hall pulse. A slowly spinning-down disc therefore shows short
drops to 0 Hz about every 2 s. The planned firmware update (protocol version 2) removes this rule.

## Installation

Python 3.11 or newer is required (the project is developed with Python 3.14).

```bash
python -m venv .venv

# macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -e ".[dev]"
```

## Running

```bash
python -m gyroscope_ui                  # start the application
python -m gyroscope_ui --simulate       # simulated device, connects on start
python -m gyroscope_ui --no-connect     # do not connect automatically on start
gyroscope-ui                            # installed command, same options
python main.py                          # from the repository root, same options
```

By default the application connects to the real device on start (`application.auto_connect` in
`gyroscope_ui/config.json`, default true). `--no-connect` turns this off.

## A first measurement

1. Connect the PC to the WiFi `Kreisel-<DEVICE_ID>` of the unit. The application does not manage
   WiFi. The device panel shows the WiFi name as a hint.
2. Press "Verbinden" (`Ctrl+K`). The LED turns amber while connecting and green once data arrive.
   The device panel then shows the device ID, the firmware version and the protocol version.
3. Enter the group letter and the sub-group ("Untergruppe"). Both are required. The suffix is
   optional.
4. Press "Start" (`Space`). The start needs data from the device.
5. Press "Stop" (`Space` or `Esc`) when the measurement is finished.
6. Save with "Speichern …" (`Ctrl+S`). Alternatively, enable "Automatisch speichern" before the
   measurement, and the file is written when you press Stop.

After a save the data stay visible. Pressing "Start" then begins a new measurement. If a stopped
measurement is not saved yet, "Start" and "Zurücksetzen" ask before discarding it.

## Data and session

**Files.** The data folder is `~/Documents/Kreisel` by default (the home directory if there is no
`Documents` folder). It can be changed in the save panel.

- **Manual save** ("Speichern …"): the file dialog starts in a folder named after the weekday, group,
  TK and sub-group (sanitised), for example `MoATK8-Aufbau_1`. The proposed file name is
  `<YYYY_MM_DD>-<NN>-Messung.csv`.
- **Auto-save** ("Automatisch speichern"): the file is written into `<GROUP>_<Untergruppe>` (sanitised),
  for example `A_Aufbau_1`, as `<YYYY_MM_DD>-<NN>-Messung[-<Suffix>].csv`. `<NN>` is the next free
  two-digit number for that day in that folder.
- Existing files are never overwritten silently. Files are written atomically.

**CSV format.** UTF-8, comma-separated, with the header row:

```text
Time (s),Disk rotation frequency (Hz),Gyro Z rate (rad/s)
```

Values have six decimals. A missing value is an empty cell.

**JSON sidecar.** Next to every CSV there is a file with the same name and the extension `.json`
(format `gyroscope-ui-measurement/1`). It contains the measurement name, group, sub-group, start and
end time, device information, the number of samples, the duration, a quality section (lost samples,
reordered samples, device restarts, gaps) and the column names with units. The CSV stays complete
without the sidecar.

**Session and logs.** The files are stored in the per-user data directory:

- Windows: `%LOCALAPPDATA%\gyroscope-ui\`
- macOS: `~/Library/Application Support/gyroscope-ui/`
- Linux: `$XDG_DATA_HOME/gyroscope-ui/` (default `~/.local/share/gyroscope-ui/`)

The session settings are in `session.json` in this folder. The log is `logs/gyroscope_ui.log`
in the same folder. The log file rotates at 2 MB and keeps three backups.

## Documentation

- [docs/CONCEPT.md](docs/CONCEPT.md): the specification of the application.
- [docs/PROTOCOL.md](docs/PROTOCOL.md): the wire protocol between firmware and application.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): layers, threads, controllers and tests.
- [docs/MIGRATION_PLAN.md](docs/MIGRATION_PLAN.md): the work plan and the firmware changes.
- [docs/SHORTCUTS.md](docs/SHORTCUTS.md): the keyboard shortcuts, generated from the configuration.
- [docs/HARDWARE_CHECKLIST.md](docs/HARDWARE_CHECKLIST.md): the manual test list for a real unit on a
  Windows lab PC.

## Development

```bash
.venv/bin/pytest                        # all tests; hardware is never required
QT_QPA_PLATFORM=offscreen .venv/bin/pytest   # optional: UI tests without a display
.venv/bin/ruff check .
.venv/bin/ruff format .
gyroscope_ui/pyqt/pyuic.sh              # after editing a Designer .ui file (bash script)
```

On Windows use `.venv\Scripts\pytest`, `.venv\Scripts\ruff` and so on.

- The forms are built in Qt Designer (`gyroscope_ui/pyqt/*.ui`). `pyuic.sh` copies the German texts
  from `config.json` into the `.ui` files and regenerates the `*_ui.py` modules. Do not edit the
  `*_ui.py` files by hand.
- User-visible texts are German and live in `gyroscope_ui/config.json`. Code, comments, docstrings,
  logs, tests and documentation are English.
- The layers are `ui/` → `infrastructure/` → `core/`. Only `core/` is free of Qt, sockets and file
  I/O. The rules are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Firmware

The firmware is in `Arduino-Gyroscope/` (PlatformIO, C++).

```bash
cd Arduino-Gyroscope
pio run                                 # build
pio run -e <DEVICE_ID> -t upload        # OTA upload to one unit, e.g. E35433
pio run -e usb-<DEVICE_ID> -t upload    # first flash, recovery or new passwords over USB
```

The passwords are not tracked by git. Before building, create `src/secrets.h` from
`src/secrets_template.h` (WiFi password, router network(s) for OTA, OTA password) and
`secrets.ini` from `secrets.ini.template` (the same OTA password, used for the upload). An optional
second router network (`SECRET_STA_SSID2`, `SECRET_STA_PASS2`) can be set; at boot the unit joins
the stronger one in range.

## Repository layout

```text
gyroscope-ui/
├── gyroscope_ui/
│   ├── core/              pure Python and NumPy: models, protocol, recording, naming, simulation
│   ├── infrastructure/    UDP device, mock, storage, session store, config, logging, paths
│   ├── ui/                controllers, tabs, widgets, main window
│   ├── pyqt/              Qt Designer forms (*.ui) and generated *_ui.py modules
│   ├── config.json        tunables, shortcuts and German UI texts
│   └── main.py            application entry point
├── Arduino-Gyroscope/     firmware (PlatformIO)
├── docs/                  specification, protocol, architecture, checklists
├── tests/                 core, infrastructure and ui tests
├── main.py                launcher from the repository root
└── pyproject.toml         package metadata, dependencies, ruff configuration
```

## License

Apache License 2.0. See [LICENSE](LICENSE).
