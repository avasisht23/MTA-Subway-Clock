"""Fetch realtime subway arrival times from MTA GTFS feeds."""

import logging
from datetime import datetime

import pytz

from config import STATIONS, MAX_MINUTES, MAX_ARRIVALS_PER_LINE

logger = logging.getLogger(__name__)

NYC_TZ = pytz.timezone("America/New_York")

# Map feed_key to the set of (stop_id, lines) that need data from that feed.
# Multiple stations can share a feed_key (e.g., "1" covers 2/3/4/5).
def _build_feed_plan():
    """Build a plan of which feeds to fetch and what to extract from each."""
    # feed_key -> list of {"stop_id": ..., "lines": [...]}
    plan = {}
    for station in STATIONS:
        for fk in station["feed_keys"]:
            if fk not in plan:
                plan[fk] = []
            plan[fk].append({
                "stop_id": station["stop_id"],
                "lines": station["lines"],
            })
    return plan


FEED_PLAN = _build_feed_plan()


def fetch_arrivals():
    """Fetch arrival times for all configured stations.

    Returns:
        dict: line_id -> sorted list of minutes until arrival.
              e.g. {"C": [3, 8, 14], "B": [5, 12], "Q": [8], ...}
    """
    # Import here so test_feed.py can check import errors clearly
    from nyct_gtfs import NYCTFeed

    now = datetime.now(NYC_TZ)
    arrivals = {}  # line_id -> [minutes]

    for feed_key, targets in FEED_PLAN.items():
        try:
            feed = NYCTFeed(feed_key)
        except Exception as e:
            logger.error("Failed to fetch feed '%s': %s", feed_key, e)
            continue

        # Collect all stop_ids we need from this feed
        all_stop_ids = [t["stop_id"] for t in targets]

        try:
            trips = feed.filter_trips(headed_for_stop_id=all_stop_ids)
        except Exception as e:
            logger.error("Failed to filter trips for feed '%s': %s", feed_key, e)
            continue

        for trip in trips:
            route_id = trip.route_id
            for update in trip.stop_time_updates:
                # Check if this stop_time_update is for one of our target stops
                for target in targets:
                    if update.stop_id != target["stop_id"]:
                        continue
                    if route_id not in target["lines"]:
                        continue

                    arrival = update.arrival
                    if arrival is None:
                        continue

                    # Make timezone-aware if needed
                    if arrival.tzinfo is None:
                        arrival = NYC_TZ.localize(arrival)

                    minutes = (arrival - now).total_seconds() / 60

                    # Only include trains 1-MAX_MINUTES away
                    if 1 <= minutes <= MAX_MINUTES:
                        if route_id not in arrivals:
                            arrivals[route_id] = []
                        arrivals[route_id].append(int(minutes))

    # Sort and cap each line's arrivals
    for line_id in arrivals:
        arrivals[line_id] = sorted(arrivals[line_id])[:MAX_ARRIVALS_PER_LINE]

    return arrivals
