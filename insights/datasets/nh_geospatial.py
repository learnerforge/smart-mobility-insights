import json
import logging

import requests

logger = logging.getLogger(__name__)

NH_GEOJSON_URL = (
    "https://github.com/yashveeeeeeer/india-geodata/releases/download/"
    "infra/national-highways/INDIA_NATIONAL_HIGHWAY.geojson"
)
TIMEOUT = 120


def fetch_national_highways_geojson():
    try:
        resp = requests.get(NH_GEOJSON_URL, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        logger.error("Failed to fetch NH GeoJSON: %s", e)
        return None


def parse_highways(geojson):
    features = geojson.get("features", [])
    parsed = []
    for feat in features:
        props = feat.get("properties", {})
        geom = feat.get("geometry")
        if not geom:
            continue
        nh_number = props.get("NH_Number", props.get("nh_number", props.get("Name", props.get("name", ""))))
        name = props.get("Name", props.get("name", ""))
        length = props.get("Length_km", props.get("length_km"))
        parsed.append({
            "nh_number": str(nh_number),
            "name": str(name),
            "length_km": float(length) if length else None,
            "geometry": geom,
        })
    return parsed
