#!/bin/bash
# NYC Subway LED Clock - Raspberry Pi Setup Script
#
# Run this on your Pi after flashing Raspberry Pi OS:
#   chmod +x install.sh
#   ./install.sh
#
set -e

echo "=== NYC Subway LED Clock - Pi Setup ==="
echo ""

# 1. System packages
echo "[1/5] Installing system packages..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev git

# 2. Clone and build rpi-rgb-led-matrix
echo ""
echo "[2/5] Building LED matrix library..."
if [ ! -d "$HOME/rpi-rgb-led-matrix" ]; then
    cd "$HOME"
    git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
    cd rpi-rgb-led-matrix
else
    cd "$HOME/rpi-rgb-led-matrix"
    git pull
fi

# Build the C library
make -j$(nproc)

# Build and install Python bindings
cd bindings/python
make build-python PYTHON=$(which python3)
sudo make install-python PYTHON=$(which python3)

# 3. Install Python dependencies
echo ""
echo "[3/5] Installing Python dependencies..."
cd "$HOME"
pip3 install nyct-gtfs pytz

# 4. Set up the subway clock project
echo ""
echo "[4/5] Setting up subway clock..."
CLOCK_DIR="$HOME/subway-clock"
if [ ! -d "$CLOCK_DIR" ]; then
    mkdir -p "$CLOCK_DIR"
fi

# Copy project files (assumes this script is in the project directory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/config.py" "$CLOCK_DIR/"
cp "$SCRIPT_DIR/mta_feed.py" "$CLOCK_DIR/"
cp "$SCRIPT_DIR/display.py" "$CLOCK_DIR/"
cp "$SCRIPT_DIR/main.py" "$CLOCK_DIR/"
cp "$SCRIPT_DIR/test_feed.py" "$CLOCK_DIR/"

# 5. Install systemd service
echo ""
echo "[5/5] Installing systemd service..."
sudo cp "$SCRIPT_DIR/subway-clock.service" /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Wire your LED panels to the Pi GPIO (see README)"
echo "  2. Connect 5V power to the panels"
echo "  3. Test the feed:  python3 $CLOCK_DIR/test_feed.py"
echo "  4. Test the display: sudo python3 $CLOCK_DIR/main.py"
echo "  5. Enable auto-start: sudo systemctl enable subway-clock"
echo "  6. Start the service: sudo systemctl start subway-clock"
echo ""
