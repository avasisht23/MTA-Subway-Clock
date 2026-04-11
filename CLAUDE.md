# CLAUDE.md

## Project overview

NYC Subway LED Clock — a Raspberry Pi 3 + Adafruit RGB Matrix Bonnet project that displays real-time MTA subway arrivals on P6 32x16 RGB LED panels. Currently configured for Brooklyn stations (Clinton-Washington, 7 Av, Eastern Pkwy, Atlantic Av) tracking Manhattan-bound trains.

## Architecture

- **`config.py`** — All configuration: stations, stop IDs, line colors, display settings, matrix hardware params. This is the single source of truth for what stations/lines to track.
- **`mta_feed.py`** — Fetches MTA GTFS realtime feeds using the `nyct-gtfs` library. Maps feed keys to stop IDs. Returns `dict[line_id, list[int]]` (line → sorted minutes to arrival).
- **`display.py`** — Two display backends:
  - `TerminalDisplay` — ANSI color output for Mac testing (`--test` flag)
  - `LEDDisplay` — Renders to RGB LED matrix via `rgbmatrix` C library (Pi only). Draws octagon badges, station names, arrival times with custom pixel-level comma separator.
- **`main.py`** — Entry point. Fetches data every 30s, rotates display every 10s. Runs as systemd service.
- **`test_feed.py`** — Standalone feed test, no hardware needed.

## Hardware specifics

- Panel is **P6 64x32** (single panel, 64 pixels wide, 32 pixels tall)
- Uses **Adafruit RGB Matrix Bonnet** (`hardware_mapping = "adafruit-hat"`)
- Pi 3 needs `gpio_slowdown = 3`
- The `rgbmatrix` Python module was compiled manually on the Pi from `~/rpi-rgb-led-matrix` using Cython + g++. It is NOT pip-installable. The compiled `.so` files live in `~/rpi-rgb-led-matrix/bindings/python/rgbmatrix/`.
- Font used: `6x10.bdf` from `~/rpi-rgb-led-matrix/fonts/`

## Key decisions and gotchas

- **No API key needed** — MTA GTFS realtime feeds are public, `nyct-gtfs` handles the protobuf parsing.
- **Stop IDs use "N" suffix** — e.g., `A44N` means northbound (Manhattan-bound). Change to `S` for southbound.
- **Feed keys map to MTA feed URLs** — e.g., feed key `"1"` covers lines 1/2/3/4/5/6/7, key `"C"` covers A/C/E, key `"B"` covers B/D/F/M, key `"Q"` covers N/Q/R/W.
- **Running as root** — LED matrix requires root for GPIO timing. Use `setcap 'cap_sys_nice=eip'` on the Python binary to avoid needing sudo.
- **PYTHONPATH matters** — When running as root/systemd, must include both `~/rpi-rgb-led-matrix/bindings/python` and `~/.local/lib/python3.13/site-packages`. The systemd service file sets these via `Environment=` directives.
- **Font finding** — `_find_font()` needs `SUDO_USER` or `HOME` env var set correctly when running as root, otherwise `~` expands to `/root/` and fonts aren't found. The service file sets these.
- **Display rotation** — `main.py` increments `_rotation_index` on the display object every 10 seconds. The display's `update()` method uses this to pick which active line to show.
- **Comma separator** — Uses 2 hand-drawn diagonal pixels instead of the BDF font's comma character, to save horizontal space.
- **64x32 panel layout** — Two rows of subway info, each with octagon badge + station name + arrival times. Rotates through active lines in pairs every 10 seconds.

## Development workflow

1. Edit code locally on Mac
2. `scp` changed files to `avasisht@192.168.1.236:~/subway-clock/`
3. SSH into Pi and restart: `sudo systemctl restart subway-clock`
4. Check logs: `sudo journalctl -u subway-clock -f`
5. Test feed without display: `python3 test_feed.py`
6. Test display on Mac: `python3 main.py --test`

## Service management

The clock runs as a systemd service. After deploying code changes, the service must be restarted — it does not pick up file changes automatically.

- **Restart after code changes**: `sudo systemctl restart subway-clock`
- **Stop the clock**: `sudo systemctl stop subway-clock`
- **Start the clock**: `sudo systemctl start subway-clock`
- **Disable auto-start on boot**: `sudo systemctl disable subway-clock`
- **Re-enable auto-start on boot**: `sudo systemctl enable subway-clock`
- **Check status**: `sudo systemctl status subway-clock`
- **View logs**: `sudo journalctl -u subway-clock -f`

If `subway-clock.service` itself was changed, copy it and reload before restarting:
```
sudo cp ~/subway-clock/subway-clock.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart subway-clock
```

## Future work

- **Web remote control** — Flask/FastAPI server on Pi for phone-based line switching (tap to change displayed line, toggle auto-rotate, adjust brightness)
- **Enclosure** — Wood frame like reference images
- **More stations** — Add stops by finding stop IDs in MTA GTFS static `stops.txt`
- **Southbound support** — Change stop ID suffix from `N` to `S`
- **Service alerts** — Show delay/disruption info from MTA alerts feed
