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
    STATION_GROUPS,
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
    MATRIX_PIXEL_MAPPER,
    MATRIX_PANEL_TYPE,
    DARK_LETTER_LINES,
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

    def __init__(self):
        self._rotation_index = 0

    def update(self, arrivals):
        """Print current arrivals to stdout, showing one station group at a time."""
        sys.stdout.write("\033[2J\033[H")

        print("=" * 40)
        print("  NYC Subway Clock  (Manhattan-bound)")
        print("=" * 40)

        # Find station groups that have active arrivals
        active_groups = []
        for group in STATION_GROUPS:
            group_lines = [(lid, arrivals[lid]) for lid in group["lines"] if arrivals.get(lid)]
            if group_lines:
                active_groups.append((group["name"], group_lines))

        if not active_groups:
            print(f"  {ANSI_DIM}No trains{ANSI_RESET}")
        else:
            idx = self._rotation_index % len(active_groups)
            station_name, lines = active_groups[idx]
            print(f"  {ANSI_WHITE}{station_name}{ANSI_RESET}")
            for line_id, times in lines:
                color = LINE_ANSI_COLORS.get(line_id, "")
                time_str = ", ".join(f"{t} min" for t in times)
                print(f"    {color}{line_id}{ANSI_RESET}  {time_str}")
            if len(lines) == 1:
                print(f"\n  \033[94mSafe trip!\033[0m")

        print("-" * 40)
        print("\n  All stations:")
        for group in STATION_GROUPS:
            for line_id in group["lines"]:
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
        if MATRIX_PIXEL_MAPPER:
            options.pixel_mapper_config = MATRIX_PIXEL_MAPPER
        if MATRIX_PANEL_TYPE:
            options.panel_type = MATRIX_PANEL_TYPE
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
            "/home/avasisht/rpi-rgb-led-matrix/fonts/" + name,
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

    def _draw_line_row(self, y_center, line_id, times):
        """Draw one subway line's info at the given vertical center.

        Layout: [octagon badge] [station name] [arrival times]
        """
        graphics = self.graphics
        r, g, b = LINE_COLORS.get(line_id, (255, 255, 255))
        station = LINE_STATION.get(line_id, "")

        # Octagon badge centered vertically at y_center
        self._draw_octagon(7, y_center, r, g, b)

        # Line letter inside the octagon (black on light backgrounds, white otherwise)
        if line_id in DARK_LETTER_LINES:
            letter_color = graphics.Color(0, 0, 0)
        else:
            letter_color = graphics.Color(255, 255, 255)
        graphics.DrawText(self.canvas, self.font, 5, y_center + 4, letter_color, line_id)

        # Station name in green
        green = graphics.Color(0, 200, 0)
        graphics.DrawText(self.canvas, self.font, 16, y_center + 4, green, station)

        # Arrival times right-aligned with custom comma separator
        white = graphics.Color(200, 200, 200)
        panel_width = MATRIX_COLS * MATRIX_CHAIN
        char_w = 6  # 6x10.bdf font width
        show_second = len(times) >= 2 and times[0] < 10
        if not show_second:
            t1 = str(times[0])
            x = panel_width - len(t1) * char_w
            graphics.DrawText(self.canvas, self.font, x, y_center + 4, white, t1)
        else:
            t1, t2 = str(times[0]), str(times[1])
            # total width: t1 chars + 2px comma + t2 chars
            total_w = len(t1) * char_w + 2 + len(t2) * char_w
            x = panel_width - total_w
            x += graphics.DrawText(self.canvas, self.font, x, y_center + 4, white, t1)
            self.canvas.SetPixel(x, y_center + 3, 200, 200, 200)
            self.canvas.SetPixel(x - 1, y_center + 4, 200, 200, 200)
            x += 2
            graphics.DrawText(self.canvas, self.font, x, y_center + 4, white, t2)

    def update(self, arrivals):
        """Render arrivals to the LED matrix.

        64x32 layout: 2 rows, each with octagon badge + station + times.
        Rotates through station groups so all lines at one station show together.
        """
        self.canvas.Clear()
        graphics = self.graphics

        # Build active station groups (stations with at least one arriving train)
        active_groups = []
        for group in STATION_GROUPS:
            group_lines = [(lid, arrivals[lid]) for lid in group["lines"] if arrivals.get(lid)]
            if group_lines:
                active_groups.append(group_lines)

        if not active_groups:
            dim = graphics.Color(150, 150, 150)
            graphics.DrawText(self.canvas, self.font, 10, 20, dim, "No trains")
        else:
            idx = self._rotation_index % len(active_groups)
            lines = active_groups[idx]

            if len(lines) == 1:
                # Single line — top row, friendly message on bottom
                line_id, times = lines[0]
                self._draw_line_row(8, line_id, times)
                msg_color = graphics.Color(100, 100, 255)
                graphics.DrawText(self.canvas, self.font, 4, 28, msg_color, "Safe trip!")
            else:
                # Two lines — top and bottom rows
                line_id, times = lines[0]
                self._draw_line_row(8, line_id, times)
                line_id, times = lines[1]
                self._draw_line_row(24, line_id, times)

        self.canvas = self.matrix.SwapOnVSync(self.canvas)
