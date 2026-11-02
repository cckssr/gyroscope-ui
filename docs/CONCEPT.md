# Gyroscope-UI — Concept

A PySide6 application for the "Kreisel" (gyroscope) experiment of the TU Berlin lab course
(Grundpraktikum, TK8). A spinning disc carries an Arduino Nano ESP32 with an IMU and a Hall
sensor; the board streams the disc's rotation frequency and the IMU's rates over its own WiFi.
The application shows them live, records measurements and saves them as CSV files that the
students evaluate. Pure Python, runs on **Windows (lab PCs) and macOS (development)**.

This document is the specification. The device protocol is in [PROTOCOL.md](PROTOCOL.md), the
structure in [ARCHITECTURE.md](ARCHITECTURE.md), the work plan in
[MIGRATION_PLAN.md](MIGRATION_PLAN.md). Structure and UX follow `../spectrum-ui` and `../oct-ui`.

---

## 1. Facts that drive the design

| Item        | Value                                                                                                                                    |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Units       | 10 identical boards (`Kreisel-E94464`, `Kreisel-E35433 … E35441`), one per lab station                                                   |
| Link        | WiFi access point of the board, UDP, ≈ 80–100 samples/s, unreliable (loss, rare reordering)                                              |
| Channels    | device time (ms), Hall pulse frequency (Hz; = rotation frequency with one magnet), acceleration x/y/z (m/s²), angular rate x/y/z (rad/s) |
| Of interest | disc rotation frequency `f(t)` (spin-down) and the angular rate about z `ω_z(t)` (precession/nutation)                                   |
| Users       | students in groups (letter A–Z) with a sub-group label; one PC per station; German UI                                                    |
| Data flow   | CSV files in `Documents/Kreisel/…`, picked up by the lab's openBIS Dropbox folder naming                                                 |

## 2. What the current application does and what we do

| Current (1.1.x)                                                             | Gyroscope-UI 2                                                                                               |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Modal connection dialog before the main window; blocks the GUI              | "Gerät" panel in the main window (LED, Verbinden/Trennen, Simulation); connect runs off the GUI thread       |
| Demo mode via a separate mock server process and a marker file              | `--simulate` / Simulation switch: an in-process simulated gyroscope; the real UDP code is tested on loopback |
| Live values as LCDs (frequency, ω_z, point count)                           | same, plus sample rate, lost/invalid lines and data age in the status bar                                    |
| Two stacked plots (f, ω_z), points + lines, 10 Hz                           | same plots, lines only, linked x-axes, downsampling; auto-scroll window and auto-range kept                  |
| Start / Stop / Reset, Start blocked until saved or reset                    | same rules as a small state machine (section 4); confirmation instead of a silent block                      |
| Manual save via file dialog into a Dropbox-style folder                     | same folder rule (section 6.2), dialog starts there                                                          |
| Auto-save on Stop into `<Group>_<subterm>/<date>-<NN>-Messung[-suffix].csv` | same names (section 6.2), counter continues across restarts (next free number)                               |
| CSV with 3 columns                                                          | **byte-compatible 3-column CSV** + JSON metadata sidecar                                                     |
| Group fields locked after the first save until restart                      | fields stay editable while no measurement is running; values persist across restarts                         |
| Connection loss: status text, 5 reconnect attempts, then nothing            | continuous re-registration; "keine Daten" / "Verbindung verloren" states; recording marked as interrupted    |
| Hard-coded strings, unused config keys                                      | all German strings in `config.json`, all tunables used                                                       |
| No automated tests                                                          | core, infrastructure and UI tests; CI on Windows, macOS, Linux                                               |

## 3. Goals and non-goals

Goals (v2.0): everything in section 2; firmware protocol v2 (sequence numbers, correct client
handling, honest frequency); simulation mode for teaching and development; German UI
(`gyroscope_ui/config.json`); code, comments, docs, logs and tests in English.

Non-goals (v2.0): evaluation inside the app (fits of spin-down and precession: a later "Auswertung"
tab, section 11), WiFi management, direct openBIS upload, several devices at once, saving the
x/y channels to the CSV (they stay in memory and in the simulation; see section 6.1).

## 4. Measurement workflow

### 4.1 Connection states

`disconnected → connecting → connected ⇄ stale → lost`, plus `error` (connect failed: port in use,
no network). `stale` = no valid data for `device.data_timeout_s`; `lost` = none for
`device.lost_after_s`. Both recover automatically when data return. The Simulation switch can only
change while disconnected. The app starts disconnected; with `--simulate` it connects to the
simulated device on start. `application.auto_connect` (default true) connects to the real device
on start.

LED colours: off (grey) disconnected, busy (blue) connecting, ok (green) connected, warning
(orange) stale, error (red) lost/error.

### 4.2 Measurement states

| State       | Entered by                       | Start                | Stop | Reset | Save                  |
| ----------- | -------------------------------- | -------------------- | ---- | ----- | --------------------- |
| `empty`     | app start, Reset, after a save\* | yes                  | –    | –     | –                     |
| `recording` | Start                            | –                    | yes  | –     | –                     |
| `stopped`   | Stop                             | yes, asks to discard | –    | yes   | yes                   |
| `saved`     | successful save                  | yes                  | –    | yes   | yes (again, new file) |

\* After a save the data stay visible (`saved`); Start then begins a new measurement without a
question. In `stopped` (unsaved) Start and Reset ask before discarding; closing the window asks
"jetzt speichern?" (Ja / Nein / Abbrechen).

- Start requires `connected` (or `stale`, with a warning).
- Recording continues through `stale`/`lost`; the gap and its length are noted in the quality
  notes and the status bar warns. Stop is always possible.
- `recording_limit_s` (config, default 3600 s) stops a forgotten recording automatically with a
  message; memory use is bounded by it (≈ 100 samples/s × 1 h × 8 channels × 8 bytes ≈ 23 MB).

### 4.3 Data rules

- Only samples whose device time is at or after the first sample received after Start are
  recorded (no stale queued samples, D3). Time base, restart and loss rules: PROTOCOL.md section 4.
- All 8 channels are kept in memory per recorded sample (plus host receive time); the CSV writes
  the three historical columns.

## 5. Display

- **Live values** (left dock, "Live-Messwerte"): rotation frequency (Hz, 2 decimals), ω_z (rad/s,
  3 decimals), number of recorded points, recording duration (mm:ss). Updated at
  `display.rate_hz` (10 Hz) from the latest sample, also when not recording.
- **Plots** (centre): frequency over time (top) and ω_z over time (bottom), x-axes linked, x label
  "Vergangene Zeit (s)". While recording they show the recording; outside a recording they show
  a rolling preview of the last `display.preview_s` (30 s, or the scroll window if that is longer)
  so the students see the device works before pressing Start. Lines without symbols;
  `setDownsampling(auto, peak)` and `setClipToView`; redraw at `display.rate_hz`.
- The plots sit in a vertical splitter: dragging a divider changes the heights of the plots (equal
  heights again when "Alle Kanäle" adds the third plot).
- Every plot has a cursor that follows the curves: a dashed vertical line at the sample nearest to
  the mouse (in all visible plots at once), a marker on each curve and a read-out with the time
  and the values of that sample (outside the data: the time only).
- Plot controls under the plots: "Auto-Scroll" (x window follows the newest data, width
  `display.scroll_window_s`, spin box without a practical upper limit), "Auto-Range", and
  "Alle Kanäle" (adds a/g x, y, z as optional curves; off by default).
- **Status bar**: connection text, sample rate (Hz), invalid/lost counters, data age, measurement
  state; messages with level colours, timed.

## 6. Saving

### 6.1 CSV (unchanged format)

UTF-8, `csv.writer` defaults (comma, `\r\n` line ends), header row exactly:

```text
Time (s),Disk rotation frequency (Hz),Gyro Z rate (rad/s)
```

Rows: `%.6f` for each value, an empty cell for NaN. Byte-compatibility with files of version 1.1.x
is covered by a golden-file test.

### 6.2 File names and folders

Base folder: `storage.data_dir` (default `~/Documents/Kreisel`), changeable in the save panel and
persisted. Group letter: `A`–`Z` (`storage.group_letters`). Sub-group: free text, required.

- **Auto-save** (checkbox "Automatisch speichern", persisted): on Stop, into
  `<base>/<GROUP>_<subterm_sanitised>/<YYYY_MM_DD>-<NN>-<name>[-<suffix>].csv` with
  `<name>` = `storage.measurement_name` ("Messung") and `NN` = next free two-digit number in that
  folder for that day (instead of a per-process counter that restarts at 01 and could collide).
- **Manual save** (button "Speichern…", `Ctrl+S`): a file dialog starting in
  `<base>/<Wd><GROUP><TK>-<subterm_sanitised>/` (Dropbox naming, e.g. `MoATK8-Aufbau_1`) with the
  auto-save file name proposed. `<TK>` = `storage.tk` ("TK8"; 1.1.x hard-coded "TK08", which was
  wrong); `<Wd>` = German weekday abbreviation from `storage.weekday_abbreviations` (default
  `["Mo","Di","Mi","Do","Fr","Sa","So"]`, independent of the OS locale; the old `%a` gave English or
  German depending on the machine). Confirmed by the lab (2026-11-02).
- Sanitising of the sub-group (unchanged rules): characters outside `[A-Za-z0-9 _-äöüÄÖÜß]` → `_`,
  runs of `_`/space → one `_`, trimmed; longer than 20 characters → every word cut to 3 letters;
  still longer → first 16 characters + `_xxx`.
- Existing files are never overwritten silently (auto-save picks the next number, the dialog asks).
- Writes are atomic (temporary file + replace); a failed save shows the reason and leaves the
  measurement unsaved.

### 6.3 Metadata sidecar

Next to every CSV: `<same name>.json`, format `gyroscope-ui-measurement/1`, UTF-8, sorted keys:

| Key                                     | Content                                                            |
| --------------------------------------- | ------------------------------------------------------------------ |
| `format`                                | `gyroscope-ui-measurement/1`                                       |
| `dc:title`, `dc:creator`, `dc:date`     | measurement name, group name (`WiSe2026_Mo_A`), date (as in 1.1.x) |
| `group`, `subgroup`, `suffix`           | as entered                                                         |
| `start_time`, `end_time`                | ISO 8601, local time with offset                                   |
| `device`                                | id, firmware version, protocol version, simulated (bool)           |
| `application`                           | name and version                                                   |
| `samples`, `duration_s`, `mean_rate_hz` | recording statistics                                               |
| `quality`                               | invalid, reordered, estimated/exact lost, device restarts, gaps    |
| `columns`                               | the CSV column names with units                                    |

The sidecar is informational; the CSV stays self-sufficient for the students' scripts.

## 7. Simulation

`MockGyroscope` (in-process, same interface as the UDP device) produces samples from
`core/simulation.py`:

- spin-down `f(t) = f0 · exp(-t/τ)` with friction (`f0` 15 Hz, `τ` 120 s, configurable), a "kick"
  that restarts the spin (simulation panel button "Anwerfen");
- precession `ω_p = m g l / (I · 2π f)` about z, with a small nutation and seeded sensor noise;
- the v1 frequency quirk optional (`simulation.firmware_quirk`, default off);
- rate 100 Hz paced in real time × `simulation.time_scale` (tests use 0.001); loss and restart
  injection for tests (`drop_probability`, `restart_at_s`).

The simulation panel (left dock, only visible in simulation) offers "Anwerfen" and the start
frequency.

## 8. User interface

- **Window**: left dock "Steuerung" (Gerät, Live-Messwerte, Messung: Start/Stop/Reset, Speichern,
  Simulation), centre a tab widget with the "Messung" tab (plots + plot controls), status bar. The
  left dock scrolls vertically, never horizontally; the window fits 1366 × 768 (test) and 1024 px
  with the dock collapsed.
- **Toolbar** (no menu bar, it would cost a row on small screens): Verbinden/Trennen,
  Start/Stop, Speichern, Datenordner öffnen, Tastenkürzel, Über Kreisel-GUI, Beenden.
- **Shortcuts** (config `shortcuts`, one application event filter, work while a text field has
  focus): `Space` Start/Stop (not in text fields), `Ctrl+S` Speichern, `Ctrl+R` Reset, `Esc` Stop,
  `Ctrl+K` Verbinden/Trennen, `Ctrl+Shift+A` Auto-Range, `F1` Tastenkürzel. `docs/SHORTCUTS.md`
  is generated.
- **Persistence**: data folder, auto-save, display options and the window layout are restored at
  start (`session.json` in the per-user data directory). Group letter and sub-group are
  restored only on the same calendar day they were entered (the next day's group starts with
  empty fields; `session.group_valid_days`, default 1). The suffix is never persisted.

## 9. Configuration

One file `gyroscope_ui/config.json` with the sections `application`, `debug`, `device`
(address, port, timeouts, keep-alive, limits), `acquisition` (display rate, batch interval),
`simulation`, `display`, `storage`, `session`, `shortcuts`, `messages`, `ui`. Every key has a
code-side default; tests use overrides.

## 10. Firmware (protocol v2)

Changes and reasons: [PROTOCOL.md](PROTOCOL.md), section 6. The firmware keeps its own style
(German comments are kept as they are, new code English). All 10 units are flashed OTA
(`pio run -t upload -j 10`); the OTA password is separated from the WiFi password, which the
students know.

## 11. Later (not v2.0)

- "Auswertung" tab: load CSV + sidecar, fit `f(t)` (exponential / linear friction), fit the
  precession frequency against `1/f`, export the fit report.
- Direct openBIS upload instead of the Dropbox folder.
- Several simultaneous devices (teacher overview).

## 12. Implementation stages

See [MIGRATION_PLAN.md](MIGRATION_PLAN.md), section 6: 0 specification, 1 scaffold, 2 core,
3 infrastructure, 4 UI, 5 docs and review, 6 firmware, 7 hardware validation.

## 13. Lab facts and assumptions

Confirmed (2026-11-02): German weekday abbreviations, `TK8`, one magnet per disc.
`device.pulses_per_revolution` (default 1) divides the reported pulse frequency, so a later
change to several magnets is a configuration change (firmware ≥ v2 may report it in `/info`).

Still to verify:

- Lab PCs: Windows version, Python ≥ 3.11 or a packaged build, firewall rule for inbound UDP 12345.
