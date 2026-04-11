# NYC Subway LED Clock

A Raspberry Pi-powered LED display that shows real-time NYC subway arrival times for nearby stations in Brooklyn.

## What it does

- Fetches live arrival data from MTA GTFS realtime feeds every 30 seconds
- Displays subway line badge (colored octagon), station name, and minutes until next trains
- Rotates through active lines every 10 seconds
- Runs as a systemd service that starts on boot

## Hardware

- **Raspberry Pi 3** (any Pi with WiFi works)
- **Adafruit RGB Matrix Bonnet** — sits on GPIO, provides HUB75 output and DC power input
- **2x P6 32x16 RGB LED panels** — daisy-chained side by side (64x16 total)
- **5V 4A DC power supply** with 2.1mm barrel jack — powers everything through the bonnet

### Wiring

```
5V Power Supply → Bonnet DC Jack
Bonnet HUB75 → Panel 1 INPUT (left)
Panel 1 OUTPUT → Panel 2 INPUT (right)
```

No jumper wires needed — the bonnet handles all GPIO connections.

## Stations tracked

| Station | Lines | Stop ID |
|---------|-------|---------|
| Clinton-Washington | C | A44N |
| 7 Av (Park Slope) | B, Q | D25N |
| Eastern Pkwy | 2, 3 | 238N |
| Atlantic Av | 4, 5 | 235N |

All tracking Manhattan-bound (northbound) trains.

## Files

| File | Purpose |
|------|---------|
| `config.py` | Station stop IDs, MTA line colors, display settings |
| `mta_feed.py` | Fetches MTA realtime feeds, returns minutes-to-arrival per line |
| `display.py` | Two renderers: `TerminalDisplay` (Mac) + `LEDDisplay` (Pi) |
| `main.py` | Entry point with `--test` flag for terminal mode |
| `test_feed.py` | Standalone feed verification script |
| `requirements.txt` | Python dependencies |
| `install.sh` | Pi setup script (builds rpi-rgb-led-matrix, installs deps) |
| `subway-clock.service` | Systemd service for auto-start on boot |

## Setup

### Test on Mac

```bash
pip install nyct-gtfs pytz
python3 test_feed.py        # verify feed data
python3 main.py --test      # terminal display simulation
```

### Deploy on Raspberry Pi

1. Flash Raspberry Pi OS Lite (32-bit) with Raspberry Pi Imager
2. Enable SSH and WiFi in the Imager settings
3. Copy files to the Pi:
   ```bash
   scp *.py requirements.txt install.sh subway-clock.service pi@subwayclock.local:~/subway-clock/
   ```
4. SSH in and run the installer:
   ```bash
   ssh pi@subwayclock.local
   cd ~/subway-clock && chmod +x install.sh && ./install.sh
   ```
5. Build the rpi-rgb-led-matrix Python bindings (Cython + g++ compile — see install notes)
6. Test: `python3 test_feed.py`
7. Run: `python3 main.py`
8. Enable auto-start:
   ```bash
   sudo cp subway-clock.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable subway-clock
   sudo systemctl start subway-clock
   ```

### Optional Pi optimizations

```bash
# Fix color timing without needing sudo
sudo setcap 'cap_sys_nice=eip' /usr/bin/python3.13

# Dedicate a CPU core to the LED matrix
sudo bash -c 'echo -n " isolcpus=3" >> /boot/firmware/cmdline.txt'
sudo reboot
```

## Display layout

On a 64x16 pixel display (two 32x16 panels):

```
[octagon badge]  StationName  Time1,Time2
```

- Colored octagon with line letter in white (matches MTA branding)
- Station name in green
- Arrival times in white, separated by a small dot comma
- Only shows 2nd arrival time if the 1st train is under 10 minutes away

## Configuration

Edit `config.py` to change:
- **Stations**: Update `STATIONS` list with different stop IDs from MTA GTFS static data
- **Refresh rate**: `REFRESH_INTERVAL` (default 30s, matches MTA feed cadence)
- **Max minutes**: `MAX_MINUTES` (default 30, ignores trains further out)
- **Brightness**: `MATRIX_BRIGHTNESS` (0-100, default 60)
- **Panel setup**: `MATRIX_CHAIN`, `MATRIX_ROWS`, `MATRIX_COLS`
