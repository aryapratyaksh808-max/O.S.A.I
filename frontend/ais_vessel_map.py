import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import folium
from folium.plugins import Fullscreen, MeasureControl


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "ship_data.jsonl"
OUTPUT_FILE = "ship_tracking_map.html"


# ============================================================
# HELPERS
# ============================================================

def first_valid(*values):
    """Return the first value that is not None, empty, or invalid."""
    for value in values:
        if value is not None and value != "":
            return value
    return None


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_time(value):
    """Convert AIS timestamp to a sortable datetime when possible."""
    if not value:
        return None

    text = str(value).strip()

    # Handles timestamps such as:
    # 2026-09-07 20:22:45.111717535 +0000 UTC
    try:
        if text.endswith(" UTC"):
            text = text[:-4].strip()

        # Convert "+0000" to "+00:00" for fromisoformat()
        if len(text) >= 5 and text[-5] in ("+", "-") and text[-3] != ":":
            text = text[:-5] + text[-5:-2] + ":" + text[-2:]

        return datetime.fromisoformat(text)
    except ValueError:
        return None


def get_ship_name(meta, position):
    return first_valid(
        meta.get("ShipName"),
        meta.get("ship_name"),
        position.get("ShipName"),
        "Unknown"
    )


def get_mmsi(meta, position):
    return first_valid(
        meta.get("MMSI"),
        meta.get("MMSI_String"),
        position.get("UserID"),
        "Unknown"
    )


def get_coordinates(meta, position):
    """
    The uploaded AIS records contain coordinates in MetaData as
    latitude/longitude and also in Message.PositionReport as
    Latitude/Longitude. Prefer PositionReport, then fall back to MetaData.
    """

    latitude = first_valid(
        position.get("Latitude"),
        position.get("latitude"),
        meta.get("Latitude"),
        meta.get("latitude"),
        meta.get("lat"),
    )

    longitude = first_valid(
        position.get("Longitude"),
        position.get("longitude"),
        meta.get("Longitude"),
        meta.get("longitude"),
        meta.get("lon"),
    )

    latitude = to_float(latitude)
    longitude = to_float(longitude)

    if latitude is None or longitude is None:
        return None, None

    # Valid geographic coordinate check
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None, None

    return latitude, longitude


# ============================================================
# READ AIS JSONL DATASET
# ============================================================

input_path = Path(INPUT_FILE)

if not input_path.exists():
    raise FileNotFoundError(
        f"Could not find '{INPUT_FILE}'. "
        f"Put the Python file and JSONL dataset in the same folder."
    )

ships = defaultdict(list)
total_records = 0
valid_records = 0
invalid_records = 0

with input_path.open("r", encoding="utf-8") as file:
    for line_number, line in enumerate(file, start=1):

        if not line.strip():
            continue

        total_records += 1

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            invalid_records += 1
            continue

        meta = record.get("MetaData") or {}
        message = record.get("Message") or {}
        position = message.get("PositionReport") or {}

        latitude, longitude = get_coordinates(meta, position)

        if latitude is None or longitude is None:
            invalid_records += 1
            continue

        mmsi = str(get_mmsi(meta, position))
        ship_name = str(get_ship_name(meta, position))

        timestamp = first_valid(
            meta.get("time_utc"),
            position.get("Timestamp"),
            meta.get("timestamp")
        )

        point = {
            "lat": latitude,
            "lon": longitude,
            "time": timestamp,
            "datetime": parse_time(timestamp),
            "ship_name": ship_name,
            "mmsi": mmsi,
            "sog": first_valid(position.get("Sog"), position.get("SOG")),
            "cog": first_valid(position.get("Cog"), position.get("COG")),
            "heading": first_valid(position.get("TrueHeading")),
            "nav_status": position.get("NavigationalStatus"),
        }

        ships[mmsi].append(point)
        valid_records += 1


# ============================================================
# SORT EACH SHIP'S TRACK BY TIME
# ============================================================

for mmsi in ships:
    ships[mmsi].sort(
        key=lambda p: (
            p["datetime"] is None,
            p["datetime"] or datetime.min
        )
    )


# ============================================================
# FIND MAP CENTER
# ============================================================

all_points = [
    point
    for ship_points in ships.values()
    for point in ship_points
]

if not all_points:
    raise ValueError("No valid AIS coordinates were found in the dataset.")

center_lat = sum(p["lat"] for p in all_points) / len(all_points)
center_lon = sum(p["lon"] for p in all_points) / len(all_points)


# ============================================================
# CREATE MAP
# ============================================================

ship_map = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=9,
    control_scale=True,
    tiles="OpenStreetMap"
)

Fullscreen(
    position="topright",
    title="Full Screen",
    title_cancel="Exit Full Screen"
).add_to(ship_map)

MeasureControl(
    position="bottomleft",
    primary_length_unit="kilometers",
    secondary_length_unit="miles"
).add_to(ship_map)


# ============================================================
# DRAW EACH VESSEL'S TRACK
# ============================================================

for mmsi, points in ships.items():

    if not points:
        continue

    ship_name = points[0]["ship_name"]

    # One layer per vessel makes vessels individually switchable
    vessel_layer = folium.FeatureGroup(
        name=f"{ship_name} | MMSI: {mmsi}",
        show=True
    )

    # --------------------------------------------------------
    # POLYLINE: vessel movement path
    # --------------------------------------------------------

    coordinates = [
        [point["lat"], point["lon"]]
        for point in points
    ]

    if len(coordinates) >= 2:
        folium.PolyLine(
            locations=coordinates,
            weight=3,
            opacity=0.75,
            tooltip=f"{ship_name} — Track"
        ).add_to(vessel_layer)

    # --------------------------------------------------------
    # DOTS: individual AIS positions
    # --------------------------------------------------------

    for index, point in enumerate(points):

        time_text = point["time"] or "Unknown"

        popup_html = f"""
        <div style="width:280px">
            <h4 style="margin-bottom:8px">{ship_name}</h4>

            <b>MMSI:</b> {mmsi}<br>
            <b>Position:</b>
            {point["lat"]:.6f}, {point["lon"]:.6f}<br>
            <b>Time (UTC):</b> {time_text}<br>
            <b>Point:</b> {index + 1} / {len(points)}<br>
            <b>SOG:</b> {point["sog"] if point["sog"] is not None else "N/A"}<br>
            <b>COG:</b> {point["cog"] if point["cog"] is not None else "N/A"}<br>
            <b>Heading:</b> {point["heading"] if point["heading"] is not None else "N/A"}<br>
            <b>Navigation Status:</b>
            {point["nav_status"] if point["nav_status"] is not None else "N/A"}
        </div>
        """

        folium.CircleMarker(
            location=[point["lat"], point["lon"]],
            radius=4,
            weight=1,
            fill=True,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{ship_name} | {time_text}"
        ).add_to(vessel_layer)

    vessel_layer.add_to(ship_map)


# ============================================================
# OPTIONAL: MARK START AND END OF EACH TRACK
# ============================================================

start_end_layer = folium.FeatureGroup(
    name="Track Start / End",
    show=True
)

for mmsi, points in ships.items():

    if not points:
        continue

    ship_name = points[0]["ship_name"]

    # Start point
    start = points[0]

    folium.Marker(
        location=[start["lat"], start["lon"]],
        popup=(
            f"<b>START</b><br>"
            f"Ship: {ship_name}<br>"
            f"MMSI: {mmsi}<br>"
            f"Time: {start['time'] or 'Unknown'}"
        ),
        icon=folium.Icon(icon="play", prefix="fa")
    ).add_to(start_end_layer)

    # End point
    if len(points) > 1:
        end = points[-1]

        folium.Marker(
            location=[end["lat"], end["lon"]],
            popup=(
                f"<b>END / LATEST</b><br>"
                f"Ship: {ship_name}<br>"
                f"MMSI: {mmsi}<br>"
                f"Time: {end['time'] or 'Unknown'}"
            ),
            icon=folium.Icon(icon="flag", prefix="fa")
        ).add_to(start_end_layer)

start_end_layer.add_to(ship_map)


# ============================================================
# ADD LAYER CONTROL
# ============================================================

folium.LayerControl(
    collapsed=False,
    position="topright"
).add_to(ship_map)


# ============================================================
# SAVE MAP
# ============================================================

ship_map.save(OUTPUT_FILE)


# ============================================================
# SUMMARY
# ============================================================

print("\n========================================")
print("AIS VESSEL MAP CREATED SUCCESSFULLY")
print("========================================")
print(f"Input file       : {INPUT_FILE}")
print(f"Output map       : {OUTPUT_FILE}")
print(f"Total records    : {total_records}")
print(f"Valid positions  : {valid_records}")
print(f"Invalid records  : {invalid_records}")
print(f"Unique vessels   : {len(ships)}")
print(f"Map center       : {center_lat:.6f}, {center_lon:.6f}")
print("========================================")
print("\nOpen the HTML file in your browser.")
