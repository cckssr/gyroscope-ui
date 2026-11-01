# Device protocol

The wire protocol between the Kreisel firmware (`Arduino-Gyroscope/src/main.cpp`) and the host
application. Version 1 is what firmware 1.1.1 implements today; version 2 is the planned
extension (Phase 6 of [MIGRATION_PLAN.md](MIGRATION_PLAN.md)). The host must accept both.

## 1. Hardware

| Item         | Value                                                                                           |
| ------------ | ----------------------------------------------------------------------------------------------- |
| Board        | Arduino Nano ESP32                                                                              |
| IMU          | LSM6DS33 over SPI (CS 5, SCK 3, MISO 4, MOSI 6); accelerometer ±2 g, gyroscope ±250 °/s         |
| Hall sensor  | digital pin 2, `INPUT_PULLUP`, interrupt on the falling edge, dead time 1.5 ms (max ≈ 666 Hz)   |
| Device ID    | build flag `DEVICE_ID_STR` (e.g. `E35433`), one PlatformIO environment per unit                 |
| Debug output | USB serial 115200 Bd; debug mode only if a serial terminal is open within 3 s after power-up    |
| Firmware     | `SOFTWARE_VERSION` in `main.cpp`; flashed over USB (`env:usb`) or OTA (`espota`, mDNS hostname) |

## 2. Network

| Item         | Value                                                                                  |
| ------------ | -------------------------------------------------------------------------------------- |
| WiFi         | own access point, SSID `Kreisel-<DEVICE_ID>`, WPA2, channel 1, max. 4 stations         |
| Device IP    | `192.168.4.1/24` (the host gets an address from the AP's DHCP, usually `192.168.4.2…`) |
| Data         | UDP, device port **12345**                                                             |
| HTTP API     | TCP port 80 (section 5)                                                                |
| Station side | the board also joins a router (`SECRET_STA_SSID`) for OTA; not used by the application |

The host has to be connected to the device's WiFi. The application does not manage WiFi; it shows
the SSID pattern and the device address as a hint.

## 3. Version 1 (firmware ≤ 1.1.1)

### 3.1 Registration (host → device)

The host sends one UDP datagram to `192.168.4.1:12345`. The firmware ignores the payload and
stores the **source IP** in a client table:

- at most 5 entries, deduplicated by IP, never removed (until reboot);
- data is sent to every entry, always to **destination port 12345**, regardless of the source port.

Consequences for the host:

- The receiving socket must be bound to local port **12345**. If that port is taken (a second
  instance of the app, another program), no data can arrive; the host reports this
  (`device_port_in_use`) instead of falling back to another port.
- The registration payload is `CONNECT:<host_ip>:12345` for forward compatibility (version 2
  parses it). The host repeats it as a keep-alive (section 4.2); version 1 ignores the repeats.
- A sixth distinct host is silently not served until the device is rebooted.

### 3.2 Data (device → host)

One datagram per sample, about 80–100 per second (the loop ends with `delay(10)`; sensor read and
WiFi add a few ms). The payload is one ASCII line terminated by `\r\n`:

```text
<millis>,<frequency>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>\r\n
```

| #   | Field       | Type / format | Unit  | Meaning                                                                                         |
| --- | ----------- | ------------- | ----- | ----------------------------------------------------------------------------------------------- |
| 1   | `millis`    | `%lu` uint32  | ms    | `millis()` since power-up; wraps after 49.7 days                                                |
| 2   | `frequency` | `%.4f`        | Hz    | Hall pulse frequency, `1e6 / period_us`; the host divides by `device.pulses_per_revolution` (1) |
| 3–5 | `ax ay az`  | `%.4f`        | m/s²  | accelerometer (Adafruit unified sensor units)                                                   |
| 6–8 | `gx gy gz`  | `%.4f`        | rad/s | gyroscope (Adafruit unified sensor units)                                                       |

There is no header line, no sequence number and no checksum. UDP may drop or (rarely) reorder
datagrams; a datagram is never split, so a datagram is either a complete line or lost.

**Frequency quirks of version 1** (the host must not "fix" them, only document them):

- The value is the period of the **last** Hall pulse taken from an 8-entry queue, one entry per
  loop pass. Above ≈ 90 pulses/s the queue lags and overflows (stale values).
- If the value changes by less than 0.05 Hz for 2 s, the firmware reports **0.0** until it changes
  again. A steady rotation therefore reads 0 Hz after 2 s.
- Before the first pulse the value is 0.0.

### 3.3 Host-side validation

A line is accepted when:

- it decodes as ASCII and has exactly 8 (v1) or 9 (v2) comma-separated fields;
- field 1 (and field 9 in v2) is a non-negative integer, all other fields parse as finite floats;
- `0 <= frequency <= 1000` Hz, `|a| <= 200` m/s², `|g| <= 50` rad/s (generous bounds, about 10×
  the sensor ranges; config `device.limits`).

Rejected lines are counted (`invalid_lines`) and never silently turned into data. A single
datagram may contain several lines (for example from a future batching firmware); each line is
validated on its own.

## 4. Time base, loss and liveness (host rules)

### 4.1 Time

- The elapsed time of a recorded sample is `(millis - millis_at_start) / 1000` s, computed on the
  host from the device clock, not from the host's receive time (WiFi jitter would distort it).
- `millis_at_start` is the device time of the **first sample received after Start**. Samples that
  arrived before Start never enter the recording.
- **Device restart / wrap:** if `millis` decreases by more than 1 s compared with the previous
  sample, the device clock was reset. The recording continues with a new segment: the time base
  is shifted so that the elapsed time continues at `last_elapsed + nominal period`, and the
  restart is noted in the measurement's quality notes (and in the metadata). Data are never
  dropped because of a time jump.
- A small backward step (≤ 1 s, reordered datagram) drops only that one sample and counts it
  (`reordered`).

### 4.2 Liveness and keep-alive

- The host re-sends the registration every `device.keepalive_s` (2 s) while connected.
- If no valid line arrives for `device.data_timeout_s` (3 s), the connection state becomes
  "keine Daten" (warning, LED orange); the worker keeps listening and re-registering. After
  `device.lost_after_s` (15 s) the device counts as lost (LED red). Data that arrive again
  resume both states automatically. A recording running across such a gap carries a quality note.

### 4.3 Loss detection

- Version 1: the expected period is estimated from the median `millis` step of the last samples;
  gaps longer than 2.5 × the period are counted as `estimated_lost = round(gap / period) - 1`.
- Version 2: exact, from the sequence number (section 6).

## 5. HTTP API (TCP port 80)

Plain-text responses (`HTTP/1.1 200 OK`, `text/plain`, `Connection: close`). The host uses it only
to read device information after connecting (optional; failures are not errors).

| Request          | Response                                                                                                |
| ---------------- | ------------------------------------------------------------------------------------------------------- |
| `GET /version`   | software version, e.g. `1.1.1`                                                                          |
| `GET /device-id` | device ID, e.g. `E35433`                                                                                |
| `GET /info`      | lines `Device-ID: …`, `Software-Version: …`, `Uptime: … ms`, `WiFi-Status`, `IP-Adresse`, `Debug-Modus` |
| `GET /status`    | `Uptime`, `Aktuelle-Frequenz`, `Freier-Heap`, `WiFi-Signalstärke`                                       |
| anything else    | the current data line                                                                                   |

The HTTP server is served from the main loop between samples; a slow client delays the samples.
The host therefore queries it once per connection, with a 1 s timeout, never periodically.

## 6. Version 2 (planned firmware)

The new application reads v1 and v2 devices. The old application (1.1.x) rejects 9-field lines, so
**the lab PCs get the new application before any unit is flashed with v2**.

| Change         | Version 2                                                                                                                                                        |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Data line      | 9 fields: the 8 of v1 plus `seq` (`%lu` uint32, +1 per sample, wraps)                                                                                            |
| Registration   | the payload `CONNECT:<ip>:<port>` is parsed; data go to that IP **and port**; a malformed payload falls back to source IP and source port                        |
| Client table   | entries expire after 10 s without a registration (the host's keep-alive refreshes them); a full table replaces the oldest entry                                  |
| Frequency      | the queue is drained every loop pass (latest period wins); 0 Hz only after no Hall pulse for `max(2 s, 3 × last period)`; the "constant for 2 s" rule is removed |
| Identification | `GET /info` adds `Protocol: 2`                                                                                                                                   |
| OTA password   | separate from the WiFi password, not committed (see `secrets_template.h`)                                                                                        |

The host detects the version from the field count of the first valid line and from `/info`
(if reachable) and stores both in the measurement metadata.
