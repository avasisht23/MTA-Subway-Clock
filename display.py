"""Display renderers for the subway clock.

Two backends:
- TerminalDisplay: prints colored text to stdout (for testing on any computer)
- LEDDisplay: renders to RGB LED matrix via rpi-rgb-led-matrix (Pi only)
"""

import os
import sys

from config import (
    LINE_COLORS,
    LINE_ANSI_COLORS,
    LINE_STATION,
    ALL_LINES,
    ANSI_RESET,
    ANSI_WHITE,
    ANSI_DIM,
    ROW_1_LINES,
    ROW_2_LINES,
    MATRIX_ROWS,
    MATRIX_COLS,
    MATRIX_CHAIN,
    MATRIX_PARALLEL,
    MATRIX_HARDWARE,
    MATRIX_GPIO_SLOWDOWN,
    MATRIX_BRIGHTNESS,
    MATRIX_PWM_BITS,
    MATRIX_ROW_ADDR_TYPE,
    MATRIX_MULTIPLEXING,
)


def _format_row(lines, arrivals):
    """Format a row of line arrivals as a list of (line_id, text) tuples."""
    entries = []
    for line_id in lines:
        times = arrivals.get(line_id, [])
        if not times:
            continue
        if len(times) == 1:
            entries.append((line_id, f"{line_id}{times[0]}"))
        else:
            entries.append((line_id, f"{line_id}{times[0]},{times[1]}"))
    return entries


class TerminalDisplay:
    """Render subway times to the terminal with ANSI colors."""

    def update(self, arrivals):
        """Print current arrivals to stdout."""
        sys.stdout.write("\033[2J\033[H")

        print("=" * 40)
        print("  NYC Subway Clock  (Manhattan-bound)")
        print("=" * 40)

        row1 = _format_row(ROW_1_LINES, arrivals)
        if row1:
            parts = []
            for line_id, text in row1:
                color = LINE_ANSI_COLORS.get(line_id, "")
                parts.append(f"{color}{line_id}{ANSI_RESET}{ANSI_WHITE}{text[1:]}{ANSI_RESET}")
            print("  " + "  ".join(parts))
        else:
            print(f"  {ANSI_DIM}No lettered trains{ANSI_RESET}")

        row2 = _format_row(ROW_2_LINES, arrivals)
        if row2:
            parts = []
            for line_id, text in row2:
                color = LINE_ANSI_COLORS.get(line_id, "")
                parts.append(f"{color}{line_id}{ANSI_RESET}{ANSI_WHITE}{text[1:]}{ANSI_RESET}")
            print("  " + "  ".join(parts))
        else:
            print(f"  {ANSI_DIM}No numbered trains{ANSI_RESET}")

        print("-" * 40)
        print("\n  Detailed:")
        for lines_group in [ROW_1_LINES, ROW_2_LINES]:
            for line_id in lines_group:
                times = arrivals.get(line_id, [])
                if times:
                    color = LINE_ANSI_COLORS.get(line_id, "")
                    time_str = ", ".join(f"{t} min" for t in times)
                    print(f"  {color}{line_id}{ANSI_RESET}  {time_str}")
        print()


class LEDDisplay:
    """Render subway times to an RGB LED matrix."""

    # Octagon shape: 13 rows, 13px wide at widest.
    # 5 wide top/bottom, 4 diagonal steps, 5 rows at full width.
    OCTAGON_SHAPE = {
        -6: (-2, 2),
        -5: (-3, 3),
        -4: (-4, 4),
        -3: (-5, 5),
        -2: (-6, 6),
        -1: (-6, 6),
         0: (-6, 6),
         1: (-6, 6),
         2: (-6, 6),
         3: (-5, 5),
         4: (-4, 4),
         5: (-3, 3),
         6: (-2, 2),
    }

    def __init__(self):
        from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

        options = RGBMatrixOptions()
        options.rows = MATRIX_ROWS
        options.cols = MATRIX_COLS
        options.chain_length = MATRIX_CHAIN
        options.parallel = MATRIX_PARALLEL
        options.hardware_mapping = MATRIX_HARDWARE
        options.gpio_slowdown = MATRIX_GPIO_SLOWDOWN
        options.brightness = MATRIX_BRIGHTNESS
        options.pwm_bits = MATRIX_PWM_BITS
        options.row_address_type = MATRIX_ROW_ADDR_TYPE
        options.multiplexing = MATRIX_MULTIPLEXING
        options.drop_privileges = False

        self.matrix = RGBMatrix(options=options)
        self.canvas = self.matrix.CreateFrameCanvas()
        self.graphics = graphics

        self.font = graphics.Font()
        font_path = self._find_font("6x10.bdf")
        self.font.LoadFont(font_path)

        self._rotation_index = 0

    def _find_font(self, name):
        """Locate a BDF font file."""
        sudo_user = os.environ.get("SUDO_USER", "")
        candidates = [
            f"/home/{sudo_user}/rpi-rgb-led-matrix/fonts/{name}" if sudo_user else "",
            os.path.expanduser(f"~/rpi-rgb-led-matrix/fonts/{name}"),
            f"/usr/share/fonts/misc/{name}",
            f"/opt/rpi-rgb-led-matrix/fonts/{name}",
            f"fonts/{name}",
        ]
        for path in candidates:
            if path and os.path.exists(path):
                return path
        raise FileNotFoundError(f"Could not find {name} font.")

    def _draw_octagon(self, cx, cy, r, g, b):
        """Draw a filled octagon (subway line badge) on the canvas."""
        total_width = MATRIX_COLS * MATRIX_CHAIN
        for dy, (x_min, x_max) in self.OCTAGON_SHAPE.items():
            for dx in range(x_min, x_max + 1):
                px, py = cx + dx, cy + dy
                if 0 <= px < total_width and 0 <= py < MATRIX_ROWS:
                    self.canvas.SetPixel(px, py, r, g, b)

    def update(self, arrivals):
        """Render arrivals to the LED matrix.

        Rotates through active lines. Shows octagon badge, station name,
        and arrival times. Only shows 2nd arrival if 1st is under 10 min.
        """
        self.canvas.Clear()
        graphics = self.graphics

        # Collect active lines sorted by soonest arrival
        active = []
        for line_id in ALL_LINES:
            times = arrivals.get(line_id, [])
            if times:
                active.append((line_id, times))
        active.sort(key=lambda x: x[1][0])

        if not active:
            dim = graphics.Color(150, 150, 150)
            graphics.DrawText(self.canvas, self.font, 10, 13, dim, "No trains")
        else:
            self._rotation_index = self._rotation_index % len(active)
            line_id, times = active[self._rotation_index]
            r, g, b = LINE_COLORS.get(line_id, (255, 255, 255))
            station = LINE_STATION.get(line_id, "")

            # Octagon badge
            self._draw_octagon(7, 7, r, g, b)

            # Line letter in white inside the octagon
            white_letter = graphics.Color(255, 255, 255)
            graphics.DrawText(self.canvas, self.font, 5, 11, white_letter, line_id)

            # Station name in green
            green = graphics.Color(0, 200, 0)
            x = 16
            x += graphics.DrawText(self.canvas, self.font, x, 11, green, station)
            x += 3

            # Arrival times in white with custom comma separator
            white = graphics.Color(200, 200, 200)
            show_second = len(times) >= 2 and times[0] < 10
            if not show_second:
                graphics.DrawText(self.canvas, self.font, x, 11, white, str(times[0]))
            else:
                x += graphics.DrawText(self.canvas, self.font, x, 11, white, str(times[0]))
                self.canvas.SetPixel(x, 10, 200, 200, 200)
                self.canvas.SetPixel(x - 1, 11, 200, 200, 200)
                x += 2
                graphics.DrawText(self.canvas, self.font, x, 11, white, str(times[1]))

        self.canvas = self.matrix.SwapOnVSync(self.canvas)
