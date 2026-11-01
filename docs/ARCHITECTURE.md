# Architecture

How Gyroscope-UI is organised and the rules that keep it maintainable. It follows the blueprint of
`../spectrum-ui` and `../oct-ui` (three layers, controllers, one place for Qt threads, mocks next
to the device adapters, Designer forms, one configuration file). The requirements are in
[CONCEPT.md](CONCEPT.md), the wire protocol in [PROTOCOL.md](PROTOCOL.md).

## 1. Three layers

```text
ui/  ──►  infrastructure/  ──►  core/          (ui/ may also import core/ directly)
```

| Layer                          | Contains                                                                                       | Must not import               |
| ------------------------------ | ---------------------------------------------------------------------------------------------- | ----------------------------- |
| `gyroscope_ui/core/`           | models, line protocol, time base, recording, statistics, file naming, metadata, simulation     | Qt, sockets, file I/O         |
| `gyroscope_ui/infrastructure/` | device protocol, UDP adapter, mock, storage, session store, config, logging, paths, Qt threads | Qt, except in `qt_threads.py` |
| `gyroscope_ui/ui/`             | controllers, tabs, widgets, main window, i18n, shortcuts                                       | –                             |

```text
gyroscope_ui/
├── core/                      pure Python + NumPy, unit-tested
│   ├── models.py              frozen dataclasses shared by all layers (the contract)
│   ├── protocol.py            parse/validate data lines, registration payload, host:port
│   ├── timebase.py            device millis → elapsed seconds; restart, reorder and loss rules
│   ├── recording.py           Recording: chunked NumPy buffer of all channels, statistics, quality
│   ├── naming.py              auto-save names, Dropbox folder names, sanitising, group name
│   ├── csv_format.py          header and rows of the 3-column CSV (byte-compatible with 1.1.x)
│   ├── metadata.py            metadata dict of the JSON sidecar
│   └── simulation.py          spinning disc physics shared by the mock and the tests
├── infrastructure/
│   ├── devices/base.py        GyroDevice protocol, DeviceError(key, **fmt)
│   ├── devices/udp_device.py  UdpGyroDevice (socket, registration, keep-alive, HTTP info)
│   ├── devices/discovery.py   create_device(config, simulate)
│   ├── mocks/mock_gyroscope.py  MockGyroscope on core.simulation
│   ├── storage.py             atomic CSV + sidecar writer, next free file number
│   ├── session_store.py       session.json (atomic, damaged file → .bak)
│   ├── qt_threads.py          ALL Qt threads: ConnectWorker, AcquisitionWorker
│   ├── config.py, logging.py, paths.py
├── pyqt/                      Qt Designer .ui files, generated *_ui.py, pyuic.sh, sync_texts.py, preview.py
├── ui/
│   ├── context.py             AppContext handed to tabs
│   ├── session_state.py       shared, persisted state (group, folder, options, ui_state)
│   ├── controllers/           connection, measurement, save, simulation, shortcut
│   ├── tabs/                  registry + measurement tab
│   ├── widgets/               panels, plots, status_led, elided_label, vscroll, shortcuts_dialog
│   ├── windows/main_window.py
│   ├── i18n.py, messages.py, shortcuts.py, future_bridge.py
├── config.json
├── main.py, __main__.py
```

**Signals carry primitives, NumPy arrays or frozen dataclasses from `core/models.py`**, never
device objects or sockets, so queued connections across threads are safe.

**The contract is `core/models.py`:**

| Model               | Content                                                                                                             |
| ------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `Sample`            | `device_ms`, `frequency_hz`, `accel_{x,y,z}_m_s2`, `gyro_{x,y,z}_rad_s`, `seq` (or None), `host_time_s` (monotonic) |
| `SampleBatch`       | the same as read-only NumPy columns (`seq` -1 = none); what the worker emits; `CHANNELS` names the 7 float columns  |
| `LinkState`         | `disconnected`, `connecting`, `connected`, `stale`, `lost`, `error`                                                 |
| `DeviceInfo`        | `device_id`, `address`, `simulated`, `firmware_version`, `protocol_version`                                         |
| `LinkStats`         | `rate_hz`, `received`, `invalid`, `data_age_s`, `protocol_version`                                                  |
| `RecordingQuality`  | samples, reordered, estimated/exact lost, device restarts, `Gap` list; `notes()` gives message keys (sidecar)       |
| `ChannelStatistics` | count, minimum, maximum, mean, population std of one channel (NaN ignored)                                          |
| `MeasurementInfo`   | group, subgroup, suffix, start/end time, device info                                                                |

## 2. The device layer

`infrastructure/devices/base.py` defines `GyroDevice`, a runtime-checkable `Protocol`:

| Method                            | Meaning                                                                       |
| --------------------------------- | ----------------------------------------------------------------------------- |
| `info`, `is_open`                 | `DeviceInfo`; open state                                                      |
| `open()`, `close()`               | bind, register, read `/info` (best effort); release the socket                |
| `read(timeout_s) -> list[Sample]` | blocks up to `timeout_s`, returns the valid samples of the datagrams received |
| `keepalive()`                     | re-send the registration (no-op for the mock)                                 |
| `stats() -> LinkStats`            | counters since `open()`                                                       |

| Device     | Class                                       | Notes                                                                                 |
| ---------- | ------------------------------------------- | ------------------------------------------------------------------------------------- |
| Real       | `UdpGyroDevice` (`devices/udp_device.py`)   | binds local port 12345 (`device_port_in_use` otherwise), parsing in `core.protocol`   |
| Simulation | `MockGyroscope` (`mocks/mock_gyroscope.py`) | ID `SIM0001`; samples from `core/simulation.py`; `time_scale`, loss/restart injection |

Rules:

- **Errors carry message keys, not texts.** `DeviceError(key, **fmt)` with subclasses
  `DeviceTimeoutError`, `DevicePortInUseError`; `ui/messages.py` translates them from
  `config.json → messages`.
- **The adapter is thin.** Socket I/O only; parsing, validation, time base and loss estimation are
  pure functions in `core/` and tested there.
- **Loopback test.** `tests/infrastructure/fake_firmware.py` is a small UDP server on 127.0.0.1
  that behaves like firmware v1 or v2 (registration, data lines, restart, loss); the adapter is
  tested against it with a configurable device port.

## 3. Threads and the worker contract

All `QThread` subclasses are in `infrastructure/qt_threads.py`; everything else is plain Python.
All workers use a 16 MiB stack.

| Thread      | Class               | Does                                                                                   |
| ----------- | ------------------- | -------------------------------------------------------------------------------------- |
| GUI         | main thread         | widgets, controllers, plots, session state                                             |
| Connect     | `ConnectWorker`     | `device.open()` off the GUI thread                                                     |
| Acquisition | `AcquisitionWorker` | owns the open device; reads, keeps alive, tracks liveness; batches samples for the GUI |

**Contract of `AcquisitionWorker`:**

1. **One loop, one owner.** After `open()` only this thread touches the device. The loop calls
   `device.read(0.1 s)`, sends a keep-alive every `device.keepalive_s` and evaluates liveness
   (`stale`, `lost`, recovered) from the time of the last valid sample.
2. **Batches, not per-sample signals.** Samples are collected and emitted as one `SampleBatch` every
   `acquisition.batch_interval_s` (0.05 s) via `samples_ready(SampleBatch)`. The GUI thread
   therefore receives ≈ 20 signals/s regardless of the sample rate.
3. **No signal is connected twice.** Controllers connect to the worker once in `attach()` and
   disconnect in `detach()`; a reconnect creates a new worker (no "reconnect while running" path).
4. **Liveness and stats** are emitted as `link_changed(state)` and `stats_ready(LinkStats)` (1 Hz).
5. **Failure handling.** A read error that is not a timeout emits `failed(key)` and ends the loop;
   the connection controller shows the device as lost and offers a reconnect.
6. **Shutdown.** `abort()` sets an event checked every loop pass (≤ 0.1 s); the owner `wait()`s.
   A thread that does not finish is kept in a list of lingering workers and the device is closed
   only after it has finished; no running `QThread` is destroyed.

## 4. Data flow of a measurement

```text
device ─► AcquisitionWorker (worker thread): read → core.protocol → Sample list → SampleBatch
                                                                          │ samples_ready (≈ 20 Hz)
                                                                          ▼ (GUI thread)
                                              MeasurementController.on_batch
                                                 │ Recording.append (only while recording, only
                                                 │   samples with host time ≥ start; core.timebase
                                                 │   gives elapsed time, restarts, reorder, loss)
                                                 ▼
                                   live values, plots (timer, display.rate_hz)
Stop ─► Recording.stop ─► SaveController ─► core.naming + core.metadata ─► storage (atomic CSV + JSON)
```

The amount of work per batch is small (NumPy appends into preallocated chunks), so the recording
runs on the GUI thread without a separate writer. Plots read views of the recording; they are
redrawn by a timer, never per batch.

## 5. Controllers, session state and the context

| Controller              | Bridges / policy                                                                                           |
| ----------------------- | ---------------------------------------------------------------------------------------------------------- |
| `ConnectionController`  | states `disconnected / connecting / connected / stale / lost / error`; simulation switch; owns the workers |
| `MeasurementController` | Start/Stop/Reset state machine (CONCEPT 4.2), recording, live values, recording limit                      |
| `SaveController`        | manual save (dialog), auto-save on Stop, file numbers, errors, unsaved-data questions                      |
| `SimulationController`  | simulation-only commands of the mock (kick, start frequency)                                               |
| `ShortcutController`    | one application event filter for all key bindings                                                          |

Rules:

1. **Guard first.** A controller refuses commands not allowed in the current state and reports
   through `message(level, text)` instead of raising.
2. **Widgets never call workers;** panels emit signals that the controller binds (`bind_panel`).
3. **One writer per resource.** Only the connection controller opens/closes the device; only the
   session state owns shared values; only `storage.py` writes measurement files.

`SessionState` owns the shared, persisted values (group letter, sub-group, suffix, data folder,
auto-save, display options, `ui_state(namespace)`, window layout) with a change signal each,
restores on construction, saves debounced (`session.debounce_s`) and synchronously in
`shutdown()`. `AppContext` holds `config`, `paths`, `session`, `connection`, `measurement`,
`save`.

## 6. Tabs

Tabs are plug-ins (`TabBase`, `@TabRegistry.register`, `tab_id`, `title_key`, `order`); the main
window builds whatever is registered. v2.0 has `measurement` (10, "Messung"); a later `analysis`
tab ("Auswertung") needs no change in the main window.

## 7. Configuration, language, forms and shortcuts

- **One file, `gyroscope_ui/config.json`**; `AppConfig.get("a.b.c", default)`, `section()`,
  `text()`, `message(key, **fmt)`, `with_overrides()`; a missing or broken file yields an empty
  configuration (logged) and code-side defaults apply.
- **Language.** User-visible strings are German and live in `config.json`
  (`ui.<form>.<objectName>[@tooltip|@suffix|@prefix|@placeholder|@title]`, applied by `ui/i18n.py`);
  code, comments, docstrings, logs, tests and docs are English. Errors carry keys.
- **Units in names:** `_s`, `_ms`, `_hz`, `_rad_s`, `_m_s2`.
- **Designer forms.** `.ui` files in `gyroscope_ui/pyqt/` are the source of truth; `X.ui` →
  `X_ui.py` (`Ui_X`) generated by `pyqt/pyuic.sh` (runs `sync_texts.py` first) and never edited;
  pyqtgraph plots are promoted widgets. `python -m gyroscope_ui.pyqt.preview <form> [--watch]`
  shows a single form.
- **Shortcuts** in `config.json → shortcuts`, handled by one application event filter;
  `docs/SHORTCUTS.md` is generated (`python -m gyroscope_ui.ui.shortcuts > docs/SHORTCUTS.md`) and
  a test keeps it in sync.

## 8. Persistence

| What                  | Where                                            | Format                                   |
| --------------------- | ------------------------------------------------ | ---------------------------------------- |
| Session, window state | `<user data>/session.json`                       | JSON, `gyroscope-ui-session/1`, atomic   |
| Measurements          | user data folder (default `~/Documents/Kreisel`) | CSV (CONCEPT 6.1) + JSON sidecar, atomic |
| Logs                  | `<user data>/logs/gyroscope_ui.log`              | rotating, 2 MB × 3                       |

`<user data>` is `%LOCALAPPDATA%\gyroscope-ui`, `~/Library/Application Support/gyroscope-ui` or
`$XDG_DATA_HOME/gyroscope-ui`. `AppPaths` is injectable (tests use `tmp_path`). A damaged
`session.json` is renamed to `.bak` and never blocks the start.

## 9. Resilience

- **Connection state machine** in one owner; reconnect without restart; the simulation switch
  only while disconnected.
- **Quality, never silence.** Invalid, reordered and lost samples, device restarts and gaps are
  counted, shown in the status bar and stored in the sidecar.
- **Shutdown.** `MainWindow.shutdown()` is idempotent (from `closeEvent` and
  `QApplication.aboutToQuit`): uninstall shortcuts, stop timers, save layout, stop the recording,
  `ConnectionController.shutdown()` (abort and join workers, close the device), save the session.
- **Logging.** `get_logger(name)` children of one logger; console + rotating file; excepthook;
  `debug.level` (`off | error | info | debug | verbose`). No per-sample logging above `verbose`.

## 10. Testing

`.venv/bin/pytest`; hardware is never required.

| Directory               | What                                                                                                 |
| ----------------------- | ---------------------------------------------------------------------------------------------------- |
| `tests/core/`           | protocol, time base (restart, reorder, loss), recording, naming (golden names), metadata, simulation |
| `tests/infrastructure/` | UDP adapter against the loopback fake firmware, mock, storage (golden CSV), session store, workers   |
| `tests/ui/`             | `pytest-qt`: window, connection, measurement flow, save, shortcuts, forms, small screens, shutdown   |

UI fixtures: Qt offscreen, mock at `time_scale` 0.001, isolated `AppPaths` in `tmp_path`. Lint:
`.venv/bin/ruff check .` and `ruff format --check .` (line length 100, rules `E F W I UP B SIM`);
generated `*_ui.py` excluded. Docs and JSON are formatted with `prettier`.

## 11. Extending

- **New tab:** subclass `TabBase`, register, import in `ui/tabs/__init__.py`, title in
  `config.json → ui.tabs`, form in Qt Designer, state in `session.ui_state(tab_id)`.
- **New channel or protocol version:** extend `core/protocol.py` and `Sample`/`SampleBatch`, update
  PROTOCOL.md, add a fake-firmware mode and tests.
- **New user-visible text:** German string in `config.json`, never hard-coded; new error
  conditions get a message key.
- **New shortcut:** `config.json → shortcuts`, action in `ShortcutController`, row label in
  `ui.shortcuts_dialog`, regenerate `docs/SHORTCUTS.md`.
