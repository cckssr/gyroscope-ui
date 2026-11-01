# Migration plan: gyroscope-ui onto the oct-ui / spectrum-ui architecture

Branch: `refactor/layered-architecture` (from `dev`). Status: Phases 0-2 done; next Phase 3.

## 1. Goal

Rebuild gyroscope-ui on the architecture proven in `../oct-ui` and `../spectrum-ui`:

```text
ui/ → infrastructure/ → core/        (ui/ may also import core/ directly)
```

- `core/`: pure Python + NumPy; no Qt, no sockets, no file I/O. Frozen dataclasses in `models.py` are the contract.
- `infrastructure/`: device adapter (UDP) and mock behind one `Protocol`, storage, config, logging, paths. Qt only in `qt_threads.py`.
- `ui/`: controllers, widgets, main window. Visual structure in Qt Designer `.ui` files (`*_ui.py` generated, never edited). German strings only in `config.json`.
- `--simulate` runs the whole app without hardware; tests never need hardware.

The user-visible workflow stays the same (connect → Start → Stop → save CSV per group), so the lab instructions remain valid.

## 2. Why a rebuild on the template, not an in-place refactor

The app is small (one device, one data stream, no jobs), so the domain part is small. The current code is tightly entangled: protocol parsing sits inside the `QThread`, `DataController` holds widgets, `SaveManager` opens dialogs. Untangling it in place would cost more than re-implementing the domain logic in the template structure, and about 1 500 LOC of generic infrastructure can be copied from spectrum-ui with a package rename.

## 3. Defects found in the current code (fixed by the rebuild)

| #   | Defect                                                                                                                                    | Where                                                                 |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| D1  | `Ctrl+S` bound to both Save and Stop → ambiguous shortcut, neither fires                                                                  | `src/pyqt/mainwindow.ui` (buttonSave, buttonStop)                     |
| D2  | `multi_data_point` connected twice (callback + direct connect) and again on every reconnect → duplicated samples, duplicated CSV rows     | `src/main_window.py:89-116`, `src/device_manager.py:703-712, 849-850` |
| D3  | Samples queued before Start (old time base) can become the first recorded rows; `reset_index()` races the worker thread                   | `src/device_manager.py:486-494`, `src/main_window.py:308-311`         |
| D4  | Time-jump rule drops all data after a device reboot until the old maximum is exceeded                                                     | `src/device_manager.py:413-423`                                       |
| D5  | Mock server sends µs, client expects ms → elapsed time 1000× too large in demo mode                                                       | `scripts/mock_arduino_server.py:221`                                  |
| D6  | If binding port 12345 fails the client falls back to a random port, but the firmware always sends to 12345 → silent no-data               | `src/device_manager.py:590-597`, firmware `handleUDPClients`          |
| D7  | "6 identical characters" corruption rule rejects valid lines (e.g. `millis()` = 2000000)                                                  | `src/device_manager.py:260-263`                                       |
| D8  | Blocking connect (up to ~4 s incl. `time.sleep(1)`) on the GUI thread; `processEvents()` re-entrancy                                      | `src/connection.py:83-112`, `src/device_manager.py:565-664`           |
| D9  | Group letter stays disabled after Reset; changing group requires restarting the app                                                       | `src/main_window.py:391-392, 644-645`                                 |
| D10 | O(N) list copies per sample on the GUI thread; unbounded export list; 20 000-point symbol plots redrawn at 10 Hz                          | `src/data_controller.py:144-153`, `src/plot.py:212-226`               |
| D11 | Save errors: `mkdir` outside try; path returned even on failure                                                                           | `src/helper_classes.py:394-408`                                       |
| D12 | Dead code (LCD names, statistics, history table, legacy GM-counter device, `AlertWindow` importing a missing module, duplicate `*_ui.py`) | several                                                               |
| D13 | Packaging: `requires-python >=3.9` but code needs ≥3.10; unused deps (matplotlib, scipy, pyserial, pillow); 4 different version strings   | `pyproject.toml`, `src/__init__.py`, `config.json`                    |
| D14 | CI only checks `import gyroscope_ui`; the 3.9 matrix entry cannot pass; Read the Docs config is broken                                    | `.github/workflows/*`, `.readthedocs.yaml`                            |

## 4. Target layout

```text
gyroscope_ui/
├── core/
│   ├── models.py          Sample (t_ms, frequency_hz, accel_*_m_s2, gyro_*_rad_s), MeasurementInfo, Statistics
│   ├── protocol.py        line framing, validation, parsing (8 fields, optional sequence field), CONNECT message, host:port
│   ├── timebase.py        device millis → elapsed_s; reboot/wrap detection that resets instead of dropping (D4)
│   ├── recording.py       Recording: chunked NumPy buffer, start/stop/reset rules, statistics
│   ├── naming.py          auto-save file names, group folders, Dropbox folder name, sanitising
│   ├── simulation.py      spinning disc: exponential spin-down + precession (shared by mock and tests)
│   └── metadata.py        metadata dict for the JSON sidecar
├── infrastructure/
│   ├── devices/base.py    GyroDevice Protocol, DeviceError(key, **fmt)
│   ├── devices/udp_device.py   UdpGyroDevice: bind 12345, CONNECT, recv, liveness timeout
│   ├── devices/discovery.py    create_device(config, simulate)
│   ├── mocks/mock_gyroscope.py MockGyroscope (in-process, uses core.simulation, time_scale knob)
│   ├── storage.py         CSV writer (+ metadata sidecar), atomic writes
│   ├── qt_threads.py      ConnectWorker, AcquisitionWorker (batched samples, decimated display, reconnect)
│   ├── config.py, logging.py, paths.py   copied from spectrum-ui
├── pyqt/                  main_window.ui, connection_panel.ui, live_panel.ui, measurement_panel.ui, save_panel.ui,
│                          shortcuts_dialog.ui; *_ui.py generated; pyuic.sh, sync_texts.py, preview.py
├── ui/
│   ├── context.py, i18n.py, messages.py, shortcuts.py, session_state.py
│   ├── controllers/       connection, measurement (Start/Stop/Reset state machine), save, shortcut
│   ├── tabs/              registry + measurement tab (room for a later "Auswertung" tab)
│   ├── widgets/           live values, plots (pyqtgraph), panels, status_led, elided_label, vscroll, shortcuts_dialog
│   └── windows/main_window.py
├── config.json
├── main.py, __main__.py
tests/core/, tests/infrastructure/, tests/ui/
docs/CONCEPT.md, ARCHITECTURE.md, PROTOCOL.md, SHORTCUTS.md (generated), HARDWARE_CHECKLIST.md
```

UI change: the modal connection dialog disappears; a "Gerät" panel in the left dock (status LED, Verbinden/Trennen, Simulation switch, WiFi hint) replaces it. The app opens even without a device.

## 5. Reuse map

| Source (spectrum-ui unless noted)                                                                                    | Action                                                                     |
| -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `infrastructure/config.py`, `logging.py`, `paths.py`                                                                 | copy, rename, adjust directory properties                                  |
| `ui/i18n.py`, `messages.py`, `future_bridge.py`, `tabs/registry.py`                                                  | copy, rename                                                               |
| `ui/widgets/status_led.py`, `elided_label.py`, `vscroll.py`, `shortcuts_dialog.py`                                   | copy, rename                                                               |
| `pyqt/pyuic.sh`, `sync_texts.py`, `preview.py`                                                                       | copy, rename                                                               |
| `main.py`, `__main__.py`, root `main.py`                                                                             | copy, rename                                                               |
| `ui/shortcuts.py`, `controllers/shortcut_controller.py`                                                              | copy, replace rows/actions                                                 |
| `ui/session_state.py` (debounce, `ui_state`, layout persistence; no HDF5)                                            | adapt, JSON only                                                           |
| `controllers/connection_controller.py`, `qt_threads.py` skeleton (`_WorkerThread`, `_CommandQueue`, `ConnectWorker`) | adapt                                                                      |
| `windows/main_window.py` skeleton (injection, idempotent shutdown, docks, tabs, shortcut hints)                      | adapt                                                                      |
| `tests/ui/conftest.py`, `test_pyqt_forms.py`, `test_small_screens.py`, `test_shortcuts_doc.py`, `test_shutdown.py`   | adapt                                                                      |
| oct-ui `.github/workflows/ci.yml`, `release.yml`, `tests/ui/test_designer_forms.py`                                  | copy, rename                                                               |
| `pyproject.toml` (ruff, pytest-qt, `[tool.pyside6-project]`), `.gitignore`, `CLAUDE.md`                              | adapt; fix the `ui_*.py` vs `*_ui.py` ignore pattern found in the template |

Not copied: profiles/launcher (oct-ui), HDF5 storage, presets, calibration stores.

## 6. Phases

Each phase ends green (`.venv/bin/pytest`, `.venv/bin/ruff check .`) and in its own commit. Model per phase in brackets; review always by a fresh reviewer agent.

### Phase 0 – Specification [Opus]

- [x] `docs/CONCEPT.md`: features, workflow, file formats, decisions from §8 (spec for all later phases)
- [x] `docs/PROTOCOL.md`: firmware ↔ host protocol as implemented today (WiFi AP, UDP 12345, CONNECT datagram, 8-field CSV line, units, ~100 Hz, frequency-zero quirk)
- [x] `docs/ARCHITECTURE.md`: adapted from spectrum-ui (layers, device protocol, threads, controllers, config, tests)
- [x] `CLAUDE.md` for this repo

### Phase 1 – Scaffold [Sonnet]

- [x] Create the new package `gyroscope_ui/` next to `src/` (the old app stays untouched as reference until Phase 5), new `pyproject.toml` (requires-python ≥3.11, ruff, pytest-qt, drop unused deps), `.gitignore`
- [ ] Copy generic modules from spectrum-ui (§5, "copy" rows) with package rename
- [ ] New `config.json` layout: `application`, `debug`, `device`, `acquisition`, `simulation`, `display`, `storage`, `session`, `shortcuts`, `messages`, `ui` (German strings migrated from the old `de` section and the `.ui` literals)
- [x] CI/release workflows from oct-ui; remove `test-build.yml`, `setup.py`, `MANIFEST.in`, `requirements.txt`, `GYRO_UI.pyproject*`, `.qtcreator/`, `book.toml`, Sphinx/RTD files
- [x] Recreate `.venv` (Python 3.14 as in the sibling projects) with `pip install -e ".[dev]"`

### Phase 2 – Core [Sonnet]

- [x] `models.py`, `protocol.py`, `timebase.py`, `recording.py`, `naming.py`, `csv_format.py`, `metadata.py`, `simulation.py`
- [x] Unit tests in `tests/core/` incl. regression tests for D3, D4, D7 and the naming rules (group folder, Dropbox name with explicit German weekday table instead of `%a` locale)

### Phase 3 – Infrastructure [Sonnet; Opus reviews `qt_threads.py`]

- [ ] `devices/base.py`, `udp_device.py` (no random-port fallback, clear `DeviceError` key instead – D6), `discovery.py`
- [ ] `mocks/mock_gyroscope.py` on `core.simulation`
- [ ] `storage.py`: atomic CSV with today's 3 columns (byte-compatible header) + JSON metadata sidecar `<name>.json` (format `gyroscope-ui-measurement/1`); `qt_threads.py` (`AcquisitionWorker`: one connection per signal, samples in batches of ~50 ms, display decimated to 20-30 Hz, liveness timeout + reconnect inside the worker)
- [ ] Tests against the mock and against a loopback fake firmware (UDP on 127.0.0.1) replacing `scripts/mock_arduino_server.py`

### Phase 4 – UI [Sonnet builds forms and widgets; Opus builds controllers and main window]

- [ ] Designer forms (§4) migrated from `mainwindow.ui` / `connection.ui`; texts via `sync_texts.py`
- [ ] Controllers: connection, measurement (Start/Stop/Reset state machine, D9), save (manual + auto-save, D11), shortcut (`Space` Start/Stop, `Ctrl+S` Save, `Ctrl+R` Reset, `Esc` Stop – D1)
- [ ] Plot widget: two linked pyqtgraph plots, lines without per-point symbols, `setDownsampling`/`setClipToView` (D10)
- [ ] Session state: group letter, subterm, suffix, data folder, auto-save flag and window layout persisted across restarts
- [ ] pytest-qt tests: main window, measurement flow in simulation, save, shortcuts, forms, small screens, shutdown

### Phase 5 – Docs and review [Haiku for README/SHORTCUTS, Sonnet python-reviewer]

- [ ] README (install, `--simulate`, lab usage), generated `docs/SHORTCUTS.md`, `docs/HARDWARE_CHECKLIST.md`
- [ ] Code review pass, fix findings

### Phase 6 – Firmware [Sonnet; Opus reviews protocol changes]

- [ ] Protocol v2 in `docs/PROTOCOL.md`: 9th field sequence number (uint32, wraps); host accepts 8 (v1) and 9 (v2) fields
- [ ] Parse the CONNECT payload, send to the client's source port; expire clients without CONNECT refresh after a timeout; host re-sends CONNECT periodically as keep-alive
- [ ] Replace "frequency = 0 after 2 s without change" with a pulse timeout (no Hall pulse for N periods → 0 Hz), so a steady rotation keeps its value
- [ ] Move the OTA/WiFi password from `platformio.ini` (`--auth=…`) into an untracked `secrets.ini` / env variable; rotate the password because it is in the git history
- [ ] Bump `SOFTWARE_VERSION`; `/info` reports the protocol version; host logs it into the metadata sidecar
- [ ] `pio run` builds for all envs (CI job optional)

### Phase 7 – Hardware validation [user, in the lab]

- [ ] Run `docs/HARDWARE_CHECKLIST.md` against a real Kreisel unit on Windows with old (v1) and new (v2) firmware: connect, 10 min measurement, device reboot mid-run, WiFi out of range, two PCs on one unit, save/auto-save

## 7. Suggested improvements beyond the port

Host side (part of the phases above unless decided otherwise):

1. Persist group/subterm/folder across restarts instead of locking the fields until restart (D9).
2. JSON metadata sidecar next to each CSV (the code for it exists but is commented out); the CSV keeps its 3 columns, all 8 channels stay available in memory for display and a later evaluation tab.
3. Show data quality live: sample rate, lost/invalid lines, last-data age; warn in the status bar instead of logging only.
4. Mark a measurement as interrupted when the connection drops during recording (currently silent).
5. Statistics panel (mean/σ of frequency over a selectable range) – the code exists but is never called.
6. An "Auswertung" tab later: load a saved CSV, fit the exponential spin-down and the precession frequency vs. 1/ω (lab evaluation directly in the app).

Firmware side (Phase 6, separate commits in `Arduino-Gyroscope/`; host stays compatible with today's 8-field line):

7. Append a sequence number to each line → exact loss detection on the host.
8. Send to the client's source port / parse the CONNECT payload; expire clients after a timeout (today max 5 IPs until reboot).
9. Remove the "frequency = 0 after 2 s without change" rule or make it a separate "no pulse" flag; a steady rotation currently reads 0 Hz.
10. Move the OTA/WiFi password out of the committed `platformio.ini` (`upload_flags --auth=…`) into an untracked file.

## 8. Decisions (2026-11-01)

1. Scope: full rebuild on the template.
2. CSV format: today's 3 columns unchanged (student scripts keep working) + JSON metadata sidecar.
3. Firmware changes (§7, 7-10): in scope, Phase 6.
4. Python: `requires-python >=3.11`, `.venv` recreated on 3.14; CI tests 3.11 and 3.14.
