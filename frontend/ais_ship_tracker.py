

import asyncio
import json
import os
from datetime import datetime

import websockets

API_KEY ="704f428a663721a8fec35a1eb401426e7bf61d0a"  # Set your AISSTREAM_API_KEY environment variable







BOUNDING_BOXES = [[[25.835, -80.208], [25.603, -79.879]]]
FILTER_MESSAGE_TYPES = ["PositionReport"]
OUTPUT_FILE = "ship_data.jsonl"


async def connect_ais_stream():
    url = "wss://stream.aisstream.io/v0/stream"

    async with websockets.connect(url) as websocket:
        subscribe_message = {
            "APIKey": API_KEY,
            "BoundingBoxes": BOUNDING_BOXES,
            "FilterMessageTypes": FILTER_MESSAGE_TYPES,
        }
        await websocket.send(json.dumps(subscribe_message))
        print("Subscribed! Waiting for ship data...\n")

        async for message_json in websocket:
            message = json.loads(message_json)
            message_type = message.get("MessageType")

            if message_type == "SubscriptionConfirmation":
                print("Subscription confirmed:", message["Message"])
                continue

            meta = message.get("MetaData", {})
            mmsi = meta.get("MMSI")
            ship_name = meta.get("ShipName", "").strip()
            lat = meta.get("Latitude") or meta.get("latitude")
            lon = meta.get("Longitude") or meta.get("longitude")

            print(f"[{datetime.utcnow().isoformat()}] "
                  f"MMSI={mmsi} Ship={ship_name} Lat={lat} Lon={lon} "
                  f"Type={message_type}")

            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(message) + "\n")


if __name__ == "__main__":
    if API_KEY == "Your_api_key":
        print("Pehle AISSTREAM_API_KEY environment variable set karo!")
    else:
        asyncio.run(connect_ais_stream())
import json
import os
from datetime import datetime

import websockets

API_KEY ="704f428a663721a8fec35a1eb401426e7bf61d0a"  # Set your AISSTREAM_API_KEY environment variable







BOUNDING_BOXES = [[[25.835, -80.208], [25.603, -79.879]]]
FILTER_MESSAGE_TYPES = ["PositionReport"]
OUTPUT_FILE = "ship_data.jsonl"


async def connect_ais_stream():
    url = "wss://stream.aisstream.io/v0/stream"

    async with websockets.connect(url) as websocket:
        subscribe_message = {
            "APIKey": API_KEY,
            "BoundingBoxes": BOUNDING_BOXES,
            "FilterMessageTypes": FILTER_MESSAGE_TYPES,
        }
        await websocket.send(json.dumps(subscribe_message))
        print("Subscribed! Waiting for ship data...\n")

        async for message_json in websocket:
            message = json.loads(message_json)
            message_type = message.get("MessageType")

            if message_type == "SubscriptionConfirmation":
                print("Subscription confirmed:", message["Message"])
                continue

            meta = message.get("MetaData", {})
            mmsi = meta.get("MMSI")
            ship_name = meta.get("ShipName", "").strip()
            lat = meta.get("Latitude") or meta.get("latitude")
            lon = meta.get("Longitude") or meta.get("longitude")

            print(f"[{datetime.utcnow().isoformat()}] "
                  f"MMSI={mmsi} Ship={ship_name} Lat={lat} Lon={lon} "
                  f"Type={message_type}")

            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(message) + "\n")


if __name__ == "__main__":
    if API_KEY == "Your_api_key":
        print("Pehle AISSTREAM_API_KEY environment variable set karo!")
    else:
        asyncio.run(connect_ais_stream())