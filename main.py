#!/usr/bin/env python3
"""NYC Subway LED Clock - Main entry point.

Fetches realtime MTA subway arrivals and displays them on an LED matrix
or in the terminal (for testing).

Usage:
    sudo python3 main.py           # LED matrix mode (on Raspberry Pi)
    python3 main.py --test         # Terminal mode (testing on any computer)
"""

import argparse
import logging
import signal
import sys
import time

from config import REFRESH_INTERVAL
from mta_feed import fetch_arrivals

logger = logging.getLogger("subway_clock")


def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(description="NYC Subway LED Clock")
    parser.add_argument(
        "--test", action="store_true",
        help="Use terminal display instead of LED matrix",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    setup_logging(args.verbose)

    # Initialize display
    if args.test:
        from display import TerminalDisplay
        display = TerminalDisplay()
        logger.info("Using terminal display (test mode)")
    else:
        from display import LEDDisplay
        display = LEDDisplay()
        logger.info("Using LED matrix display")

    # Graceful shutdown
    running = True

    def handle_signal(signum, frame):
        nonlocal running
        logger.info("Shutting down...")
        running = False

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Main loop
    logger.info("Subway clock started. Refreshing every %ds.", REFRESH_INTERVAL)
    ROTATE_INTERVAL = 10  # seconds between display rotation

    arrivals = {}
    last_fetch = 0

    while running:
        now = time.time()

        # Fetch new data every REFRESH_INTERVAL seconds
        if now - last_fetch >= REFRESH_INTERVAL:
            try:
                arrivals = fetch_arrivals()
                logger.debug("Fetched arrivals: %s", arrivals)
                last_fetch = now
            except Exception:
                logger.exception("Error fetching arrivals")

        # Update display (rotates to next line)
        try:
            display.update(arrivals)
            if hasattr(display, '_rotation_index'):
                display._rotation_index += 1
        except Exception:
            logger.exception("Error updating display")

        # Sleep until next rotation
        for _ in range(ROTATE_INTERVAL * 2):
            if not running:
                break
            time.sleep(0.5)

    logger.info("Subway clock stopped.")


if __name__ == "__main__":
    main()
