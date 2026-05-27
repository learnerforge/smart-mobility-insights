import logging
import time

import requests

logger = logging.getLogger(__name__)

OSRM_BASE = "https://router.project-osrm.org"
NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
_last_nominatim = 0

_session = requests.Session()
_session.headers.update({"User-Agent": "SmartMobility/1.0"})
_session_nominatim = requests.Session()
_session_nominatim.headers.update({"User-Agent": "SmartMobility/1.0"})


def geocode(query):
    global _last_nominatim
    now = time.time()
    if now - _last_nominatim < 1.0:
        time.sleep(1.0 - (now - _last_nominatim))
    url = f"{NOMINATIM_BASE}/search"
    params = {"q": query, "format": "json", "limit": 5, "addressdetails": 1}
    try:
        resp = _session_nominatim.get(url, params=params, timeout=10)
        resp.raise_for_status()
        _last_nominatim = time.time()
        return resp.json()
    except requests.RequestException as e:
        logger.error("Nominatim geocode failed for '%s': %s", query, e)
        raise


def reverse_geocode(lat, lng):
    url = f"{NOMINATIM_BASE}/reverse"
    params = {"lat": lat, "lon": lng, "format": "json"}
    try:
        resp = _session_nominatim.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error("Nominatim reverse geocode failed for %s,%s: %s", lat, lng, e)
        raise


def get_routes(origin_lat, origin_lng, dest_lat, dest_lng):
    coords = f"{origin_lng},{origin_lat};{dest_lng},{dest_lat}"
    url = f"{OSRM_BASE}/route/v1/driving/{coords}"
    params = {
        "alternatives": "true",
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }
    try:
        resp = _session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error("OSRM routing failed for %s: %s", coords, e)
        raise
