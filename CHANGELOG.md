# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

Releases are cut by the [Release (prepare)](.github/workflows/release-prepare.yml) workflow, which moves the notes under `[Unreleased]` into a dated version section. See [docs/RELEASING.md](docs/RELEASING.md).

## [Unreleased]

## [2.0.0] - 2026-11-02

Rebuild of the application on the layered architecture of oct-ui / spectrum-ui (`docs/CONCEPT.md`) together with protocol version 2 of the firmware.

### Added

- Layered package `gyroscope_ui` (`core` / `infrastructure` / `ui`) with a simulated device (`--simulate`) and a loopback fake firmware for the tests.
- Protocol v2 (firmware 2.0.0): sequence number per sample for exact loss detection, `CONNECT:<ip>:<port>` registration with keep-alive, pulse timeout instead of the 2 s "frequency = 0" rule. The host still understands protocol v1.
- Measurement tab with start / stop / reset, live values, a rolling preview before the first measurement, linked plots with an optional acceleration plot ("Alle Kanäle"), auto-scroll with a window of any length, and a crosshair cursor in every plot.
- Saving: manual and automatic, CSV byte-compatible with 1.1.x plus a JSON sidecar with the metadata (device, firmware and protocol version, quality statistics).
- Session state (group, sub-group, data folder, window layout) restored on start; keyboard shortcuts (`docs/SHORTCUTS.md`).

### Changed

- No menu bar: all actions (including "Datenordner öffnen", "Tastenkürzel", "Über Kreisel-GUI" and "Beenden") are in the toolbar, which saves a row on small screens.
- The plots sit in a splitter; the dividers between them change the plot heights.
- The cursor in the plots snaps to the nearest sample and shows the time and the values of the visible curves there, with a marker on each curve.
- The three live displays have the same digit count and size, and the decimal point takes no digit's space, so ω_z is as readable as the frequency.
- The modal connection dialog is replaced by a "Gerät" panel; the application starts without a device.
- The `GET /info` request to the device is retried, so the device ID and firmware version are no longer lost when the first request is dropped.
- Form fields in the control panels grow with the panel on macOS.

### Fixed

- The saved measurement metadata keeps the UTC offset of timezone-aware times instead of converting them to the local zone of the machine.

