"""Configuration for the NYC Subway LED Clock."""

# --- Station Definitions ---
# Each station has: stop_id (northbound), lines served, feed key(s), display name
# Stop IDs verified from MTA GTFS static data (stops.txt)
STATIONS = [
    {
        "stop_id": "A44N",
        "lines": ["C"],
        "feed_keys": ["C"],
        "name": "Clinton-Washington",
    },
    {
        "stop_id": "D25N",
        "lines": ["B", "Q"],
        "feed_keys": ["B", "Q"],
        "name": "7 Av",
    },
    {
        "stop_id": "238N",
        "lines": ["2", "3"],
        "feed_keys": ["1"],
        "name": "Eastern Pkwy",
    },
    {
        "stop_id": "235N",
        "lines": ["4", "5"],
        "feed_keys": ["1"],
        "name": "Atlantic Av",
    },
]

# --- MTA Line Colors (official) ---
LINE_COLORS = {
    "C": (0, 98, 207),      # Blue (8th Ave)
    "B": (235, 104, 0),     # Orange (6th Ave)
    "Q": (246, 188, 38),    # Yellow (Broadway)
    "2": (216, 34, 51),     # Red (7th Ave)
    "3": (216, 34, 51),     # Red (7th Ave)
    "4": (0, 153, 82),      # Green (Lexington)
    "5": (0, 153, 82),      # Green (Lexington)
}

# Lines that use black letter on light-colored badge (matches MTA style)
DARK_LETTER_LINES = {"Q"}

# ANSI color codes for terminal display (closest match to MTA colors)
LINE_ANSI_COLORS = {
    "C": "\033[34m",     # Blue
    "B": "\033[33m",     # Yellow/Orange
    "Q": "\033[93m",     # Bright Yellow
    "2": "\033[31m",     # Red
    "3": "\033[31m",     # Red
    "4": "\033[32m",     # Green
    "5": "\033[32m",     # Green
}
ANSI_RESET = "\033[0m"
ANSI_WHITE = "\033[97m"
ANSI_DIM = "\033[2m"

# --- Display Settings ---
REFRESH_INTERVAL = 30    # seconds between feed refreshes
MAX_MINUTES = 30         # ignore trains more than this many minutes away
MAX_ARRIVALS_PER_LINE = 2  # max arrival times to track per line

# --- LED Matrix Settings (single 64x32 panel) ---
MATRIX_ROWS = 32
MATRIX_COLS = 64
MATRIX_CHAIN = 1          # 1 panel
MATRIX_PARALLEL = 1
MATRIX_HARDWARE = "adafruit-hat"  # Adafruit RGB Matrix Bonnet
MATRIX_GPIO_SLOWDOWN = 4    # P3 panels need higher slowdown than P6
MATRIX_BRIGHTNESS = 60      # 0-100, keep moderate to reduce power draw
MATRIX_PWM_BITS = 7         # Lower = faster refresh, less color depth
MATRIX_ROW_ADDR_TYPE = 0    # Address type (0=default)
MATRIX_MULTIPLEXING = 0     # Multiplexing (0=default)
MATRIX_PIXEL_MAPPER = ""    # Pixel mapper (leave empty for single panel)
MATRIX_PANEL_TYPE = ""         # FM6124 chip needs no special init

# --- Display Layout ---
# All lines to display, in priority order
ALL_LINES = ["C", "B", "Q", "2", "3", "4", "5"]

# Station groups for display rotation — each entry is shown together
STATION_GROUPS = [
    {"name": "Clinton-Wash", "lines": ["C"]},
    {"name": "7 Av",         "lines": ["B", "Q"]},
    {"name": "Eastern Pkwy", "lines": ["2", "3"]},
    {"name": "Atlantic Av",  "lines": ["4", "5"]},
]

# Short station names for LED display (max ~5 chars)
LINE_STATION = {
    "C": "C-Wa",
    "B": "7 Av",
    "Q": "7 Av",
    "2": "E Pk",
    "3": "E Pk",
    "4": "Atlc",
    "5": "Atlc",
}
