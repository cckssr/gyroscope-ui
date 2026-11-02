# Hardware checklist: Kreisel unit

Manual test list for one real Kreisel unit on a Windows lab PC. Run sections 1 to 12 with the
current firmware (version 1, 1.1.1), then run them again after the firmware update (version 2)
and also run section 13. The automated tests use the simulation and a loopback fake firmware, so
these steps are the only check against real hardware. Work through the sections in order and stop
at the first failure that later steps depend on. Record every failure in the results table.

## Ground rules

- Record the unit ID (`Kreisel-<DEVICE_ID>`), the firmware version, the OS and the tester for each run.
- Only one instance of the application may use UDP port 12345 on the PC. Close any other instance or program that uses it first.
- Note the expected values as you go; the expected results come from [PROTOCOL.md](PROTOCOL.md) and [CONCEPT.md](CONCEPT.md).

## 1. Setup and prerequisites

- [ ] The lab PC runs Windows and has Python 3.11 or newer (`python --version`).
- [ ] The repository is checked out, `python -m venv .venv` has been run, and `.venv\Scripts\python -m pip install -e ".[dev]"` completes without errors.
- [ ] `.venv\Scripts\python -m pytest` passes on this PC.
- [ ] The Windows firewall allows the application to receive UDP port 12345 (open point in CONCEPT.md, section 13; if no data arrive later, check this first).
- [ ] The unit is powered on and its DEVICE_ID and firmware version are known (from `http://192.168.4.1/info` in a browser while connected to its WiFi).
- [ ] The disc has one magnet (the configuration `device.pulses_per_revolution` is 1).

## 2. Connect

- [ ] Start with `.venv\Scripts\python -m gyroscope_ui --no-connect`: the LED is grey and the device panel shows "Nicht verbunden".
- [ ] Connect the PC's WiFi to `Kreisel-<DEVICE_ID>`.
- [ ] Press "Verbinden" (`Ctrl+K`): the LED turns amber ("Verbinde …") and then green ("Verbunden, Daten kommen an") within a few seconds.
- [ ] The device line in the device panel shows `<DEVICE_ID> · Firmware <version> · Protokoll <n>` and matches `/info` of the unit (protocol 1 for version 1, protocol 2 for version 2).
- [ ] The status bar shows a sample rate of about 80 to 100 "Messwerte/s" while connected.
- [ ] The status bar shows no invalid lines ("ungültige Zeilen") during the first minute.
- [ ] Press "Trennen" (`Ctrl+K`): the LED turns grey and the status text "Nicht verbunden" appears.

## 3. Live values and plot plausibility

- [ ] With the disc at rest, the rotation frequency shows 0.00 Hz.
- [ ] Version 1 only: while the disc spins down slowly, the frequency drops briefly to 0 Hz about every 2 s (known firmware quirk, see README).
- [ ] Spin the disc by hand: the rotation frequency rises to a plausible value with two decimals (Hz).
- [ ] Count the revolutions for 10 s by hand (one magnet, so one pulse per revolution) and compare roughly with the displayed frequency.
- [ ] Stop the disc: the displayed frequency drops; note how long this takes.
- [ ] Turn the disc about its vertical axis: ω_z shows a clearly non-zero value with three decimals (rad/s).
- [ ] Reverse the rotation direction: the sign of ω_z changes.
- [ ] Before Start, the plots show a rolling preview of the last 30 s and the x-axis label "Zeit relativ zu jetzt (s)".
- [ ] With "Auto-Scroll" checked, the plot window follows the newest data; with it unchecked it does not.
- [ ] A scroll window longer than 30 s (e.g. 120 s) is honoured in the preview as well as in the recording.
- [ ] "Auto-Range" fits the axes to the data.
- [ ] Moving the mouse over the plots shows a crosshair with time and value; the vertical line is shown in all plots at once and disappears when the mouse leaves.
- [ ] With "Alle Kanäle" checked, the acceleration and the other rate curves appear; unchecked, they disappear.

## 4. Ten-minute measurement

- [ ] Enter a group letter and a sub-group (for example "Hardware Test"), then press "Start": the state shows "Messung läuft".
- [ ] Let the measurement run for 10 minutes while the disc spins.
- [ ] The status bar rate stays at about 100 "Messwerte/s" (80 to 100 expected) for the whole run.
- [ ] The data point count ("Datenpunkte") reaches about 48 000 to 60 000 after 10 minutes.
- [ ] The duration ("Dauer (mm:ss)") shows 10:00 at the end.
- [ ] The plots show no gaps and the status bar shows no warning.
- [ ] Press "Stop": the state shows "Gestoppt, nicht gespeichert".

## 5. Device reboot mid-run

- [ ] Start a recording and let it run for about 2 minutes.
- [ ] Power-cycle or reset the unit while the recording runs.
- [ ] During the outage, after about 3 s without data, the LED turns amber and the status text reads "Keine Daten – WLAN prüfen".
- [ ] After the unit has rebooted, the connection is restored without pressing "Verbinden" and the recording continues.
- [ ] Stop the measurement and save it: the note "Das Gerät wurde während der Messung neu gestartet" appears and the JSON sidecar lists the device restart in its quality section.
- [ ] The elapsed time in the CSV continues without a jump backwards at the restart.

## 6. WiFi out of range and back

- [ ] Connect and start a recording, then switch off the PC's WiFi or move the PC out of range.
- [ ] After about 3 s without data the LED turns amber and the status text reads "Keine Daten – WLAN prüfen".
- [ ] After about 15 s without data the LED turns red and the status text reads "Verbindung verloren".
- [ ] Switch the WiFi back on and reconnect to `Kreisel-<DEVICE_ID>`: the state returns to green without pressing "Verbinden".
- [ ] The recording continues through the outage and the notice "Die Verbindung ist während der Messung abgerissen" appears.
- [ ] Stop and save: the sidecar records the gap in its quality section.

## 7. Two PCs on one unit

- [ ] PC A is connected to the unit and receives data.
- [ ] PC B connects to `Kreisel-<DEVICE_ID>`, presses "Verbinden", and receives data as well.
- [ ] Both PCs show green LEDs and comparable frequency values.
- [ ] Close the application on PC B: PC A keeps receiving data without a gap.

## 8. Manual save

- [ ] Stop a measurement and press "Speichern …" (`Ctrl+S`): the dialog starts in a folder named `<Wd><GROUP>TK8-<Untergruppe>`, for example `MoATK8-Aufbau_1`.
- [ ] The proposed file name is `<YYYY_MM_DD>-<NN>-Messung.csv`.
- [ ] After saving, the state shows "Gespeichert" and the status bar shows "Daten gespeichert in …".
- [ ] A file with the same name and the extension `.json` is written next to the CSV.
- [ ] Save the same measurement again: a new file is created and nothing is overwritten.
- [ ] Choose an existing file name in the dialog: the application asks or refuses; no file is overwritten silently.
- [ ] Open the CSV in a text editor: the header is exactly `Time (s),Disk rotation frequency (Hz),Gyro Z rate (rad/s)`, there are three columns and six decimals per value.
- [ ] A student's evaluation script reads the CSV without changes.
- [ ] The JSON sidecar contains the format `gyroscope-ui-measurement/1`, the group, the sub-group, the start and end time with offset, the device (ID, firmware, protocol, simulated false), the sample count and the duration.

## 9. Auto-save

- [ ] Check "Automatisch speichern", then record and press Stop: the file is written without a dialog into `<GROUP>_<Untergruppe>` inside the data folder.
- [ ] The file name is `<YYYY_MM_DD>-01-Messung.csv` with the `.json` sidecar.
- [ ] With the suffix "Test", the file name contains `-Test` before the extension.
- [ ] A second auto-saved measurement on the same day uses number 02.
- [ ] Restart the application and auto-save again: the number continues with the next free number.
- [ ] A sub-group "Aufbau/ 1" gives the folder name `Aufbau_1` (characters outside the allowed set become `_`, runs of `_` and spaces become one `_`).
- [ ] Uncheck "Automatisch speichern": Stop no longer writes a file.

## 10. Session

- [ ] Set the group letter, the sub-group, the suffix and the data folder, then close and restart the application on the same day: all four are restored.
- [ ] On the next calendar day the group letter, sub-group and suffix are empty; the data folder and the auto-save setting are still restored.
- [ ] The file `session.json` exists in `%LOCALAPPDATA%\gyroscope-ui\`.
- [ ] The log file `logs\gyroscope_ui.log` exists in the same folder and records the start of the application.

## 11. Shortcuts

- [ ] With no button or text field focused, `Space` starts and stops a measurement.
- [ ] With the cursor in the "Untergruppe" field, `Space` types a space and does not start or stop the measurement.
- [ ] With the cursor in the "Untergruppe" field, `Ctrl+S`, `Ctrl+R` and `Ctrl+K` still work.
- [ ] `Esc` stops a running measurement.
- [ ] `Ctrl+Shift+A` runs Auto-Range.
- [ ] `Ctrl+1` switches to the "Messung" tab.
- [ ] `F1` opens the list of shortcuts ("Tastenkürzel").

## 12. Closing with unsaved data

- [ ] Stop a measurement without saving and close the window: the dialog "Ungespeicherte Messdaten" asks whether to save now.
- [ ] "Abbrechen" keeps the window open with the data still there.
- [ ] "Nein" closes the application without saving.
- [ ] "Ja" saves the measurement first.
- [ ] After a successful save, closing the window shows no dialog.

## 13. Version 2 only (after the firmware update)

- [ ] `http://192.168.4.1/info` shows `Protocol: 2` and the new software version.
- [ ] The device line in the device panel shows protocol 2 for this unit.
- [ ] A connection of several minutes shows no invalid lines and no gaps (the registration keep-alive refreshes the device's client table).
- [ ] Constant rotation: spin the disc at a constant speed for more than 2 minutes; the frequency stays at the rotation value and does not drop to 0 Hz.
- [ ] Short outage during a recording (as in section 6): the sidecar quality section reports the lost samples as an exact count, not an estimate.
- [ ] Client timeout: after closing the application on PC B, PC B's registration expires after the client timeout; PC A is not affected. If the device's serial output is not available, mark this item "not checked".
- [ ] Sidecar device section shows protocol 2 for the recorded measurement.

## Results

Result: `pass`, `fail` or `not checked`. Add one row per test run.

| Date | Unit ID | Firmware version | OS  | Tester | Result | Notes |
| ---- | ------- | ---------------- | --- | ------ | ------ | ----- |
|      |         |                  |     |        |        |       |
