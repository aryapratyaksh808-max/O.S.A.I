

import json
from datetime import datetime, timedelta

SPILL_TIME = datetime.fromisoformat("2026-09-08T13:22:00+00:00")
SPILL_LAT, SPILL_LON = 25.77, -80.18
TIME_WINDOW = timedelta(minutes=30)
DISTANCE_THRESHOLD = 0.05  # roughly ~5 km in degrees

suspects = []
with open("ship_data.jsonl") as f:
    for line in f:
        record = json.loads(line)
        meta = record.get("MetaData", {})
        if not meta.get("time_utc"):
            continue

        ship_time = datetime.fromisoformat(meta["time_utc"].split(" +")[0].replace(" ", "T") + "+00:00")
        lat = meta.get("latitude")
        lon = meta.get("longitude")

        if lat is None or lon is None:
            continue

        time_diff = abs((ship_time - SPILL_TIME).total_seconds())
        distance = ((lat - SPILL_LAT)**2 + (lon - SPILL_LON)**2) ** 0.5

        if time_diff <= TIME_WINDOW.total_seconds() and distance <= DISTANCE_THRESHOLD:
            suspects.append(meta.get("ShipName", "Unknown"))

print("Possible suspect ships:", set(suspects))