#!/usr/bin/env python3
"""Test script to verify MTA realtime feed data.

Run this on your Mac (no hardware needed) to confirm subway data is flowing:
    pip install nyct-gtfs pytz
    python test_feed.py
"""

import sys
from datetime import datetime

import pytz

from config import (
    STATIONS,
    LINE_ANSI_COLORS,
    ANSI_RESET,
    ANSI_WHITE,
    ANSI_DIM,
    ROW_1_LINES,
    ROW_2_LINES,
)
from mta_feed import fetch_arrivals

NYC_TZ = pytz.timezone("America/New_York")


def main():
    now = datetime.now(NYC_TZ)
    print(f"\n  NYC Subway Clock - Feed Test")
    print(f"  {now.strftime('%A %B %d, %Y  %I:%M:%S %p %Z')}")
    print("=" * 50)
    print("  Fetching realtime feeds (4 HTTP requests)...")
    print()

    try:
        arrivals = fetch_arrivals()
    except Exception as e:
        print(f"  ERROR: {e}")
        print(f"\n  Make sure you have nyct-gtfs installed:")
        print(f"    pip install nyct-gtfs pytz")
        sys.exit(1)

    if not arrivals:
        print("  WARNING: No arrival data received.")
        print("  This could mean:")
        print("    - MTA feeds are temporarily down")
        print("    - No trains running right now (late night?)")
        print("    - Network connectivity issue")
        sys.exit(1)

    # Print per-station breakdown
    for station in STATIONS:
        print(f"  {station['name']} (stop: {station['stop_id']}):")
        has_data = False
        for line_id in station["lines"]:
            times = arrivals.get(line_id, [])
            color = LINE_ANSI_COLORS.get(line_id, "")
            if times:
                time_str = ", ".join(f"{t} min" for t in times)
                print(f"    {color}{line_id}{ANSI_RESET}  {ANSI_WHITE}{time_str}{ANSI_RESET}")
                has_data = True
            else:
                print(f"    {ANSI_DIM}{line_id}  (no trains){ANSI_RESET}")
        if not has_data:
            print(f"    {ANSI_DIM}No trains found for this station{ANSI_RESET}")
        print()

    # Show compact display preview
    print("-" * 50)
    print("  LED Display Preview (what you'll see on the matrix):")
    print()

    # Row 1: Lettered lines
    row1_parts = []
    for line_id in ROW_1_LINES:
        times = arrivals.get(line_id, [])
        if times:
            color = LINE_ANSI_COLORS.get(line_id, "")
            if len(times) == 1:
                row1_parts.append(f"{color}{line_id}{ANSI_RESET}{ANSI_WHITE}{times[0]}{ANSI_RESET}")
            else:
                row1_parts.append(f"{color}{line_id}{ANSI_RESET}{ANSI_WHITE}{times[0]},{times[1]}{ANSI_RESET}")

    # Row 2: Numbered lines
    row2_parts = []
    for line_id in ROW_2_LINES:
        times = arrivals.get(line_id, [])
        if times:
            color = LINE_ANSI_COLORS.get(line_id, "")
            if len(times) == 1:
                row2_parts.append(f"{color}{line_id}{ANSI_RESET}{ANSI_WHITE}{times[0]}{ANSI_RESET}")
            else:
                row2_parts.append(f"{color}{line_id}{ANSI_RESET}{ANSI_WHITE}{times[0]},{times[1]}{ANSI_RESET}")

    print(f"  Row 1:  {'  '.join(row1_parts) if row1_parts else '(empty)'}")
    print(f"  Row 2:  {'  '.join(row2_parts) if row2_parts else '(empty)'}")
    print()

    # Summary
    total_lines = len(arrivals)
    total_trains = sum(len(v) for v in arrivals.values())
    print(f"  Feed OK: {total_lines} lines active, {total_trains} trains tracked")
    print()


if __name__ == "__main__":
    main()
