import logging
import math
from datetime import datetime

from .utils import load_config

logger = logging.getLogger(__name__)


def _to_minutes(t):
    try:
        parts = t.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, IndexError, AttributeError):
        logger.warning("Invalid time value in config: %s", t)
        return 0


def get_time_factor(config):
    now = datetime.now()
    current = now.hour * 60 + now.minute
    tc = config["traffic"]

    ms = _to_minutes(tc["peak_hours"]["morning"]["start"])
    me = _to_minutes(tc["peak_hours"]["morning"]["end"])
    es = _to_minutes(tc["peak_hours"]["evening"]["start"])
    ee = _to_minutes(tc["peak_hours"]["evening"]["end"])

    if (ms <= current <= me) or (es <= current <= ee):
        return tc["congestion_factors"]["peak"]
    elif current < 360 or current > 1320:
        return tc["congestion_factors"]["night"]
    elif (me < current < me + 60) or (ee < current < ee + 60):
        return tc["congestion_factors"]["shoulder"]
    else:
        return tc["congestion_factors"]["off_peak"]


def get_congestion_level(factor, config):
    th = config["traffic"]["congestion_thresholds"]
    if factor < th["light"]:
        return "light", "green_circle"
    elif factor < th["moderate"]:
        return "moderate", "yellow_circle"
    elif factor < th["heavy"]:
        return "heavy", "orange_circle"
    else:
        return "congested", "red_circle"


def _haversine(lat1, lng1, lat2, lng2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_area_factor(origin_lat, origin_lng, dest_lat, dest_lng, congestion_logs):
    mid_lat = (origin_lat + dest_lat) / 2
    mid_lng = (origin_lng + dest_lng) / 2
    radius = max(_haversine(origin_lat, origin_lng, dest_lat, dest_lng) / 2, 3)
    count = 0
    for log in congestion_logs:
        log_lat = log.get("lat")
        log_lng = log.get("lng")
        if log_lat is not None and log_lng is not None:
            dist = _haversine(mid_lat, mid_lng, float(log_lat), float(log_lng))
            if dist <= radius:
                count += 1
    if count > 15:
        return 2.0
    elif count > 8:
        return 1.5
    elif count > 3:
        return 1.2
    return 1.0


def get_traffic_info(
    origin_name, dest_name, congestion_logs=None,
    origin_lat=None, origin_lng=None, dest_lat=None, dest_lng=None,
):
    config = load_config()
    time_factor = get_time_factor(config)
    area_factor = get_area_factor(
        origin_lat or 0, origin_lng or 0, dest_lat or 0, dest_lng or 0,
        congestion_logs or [],
    )
    combined = max(time_factor, area_factor)
    weather_factor = 0.0
    weather_desc = None
    if origin_lat is not None:
        mid_lat = (origin_lat + (dest_lat or origin_lat)) / 2
        mid_lng = (origin_lng + (dest_lng or origin_lng)) / 2
        from .weather import get_weather_factor
        weather_factor, weather_desc = get_weather_factor(mid_lat, mid_lng)
    combined += weather_factor
    level, icon = get_congestion_level(combined, config)
    return {
        "factor": round(combined, 2),
        "level": level,
        "icon": icon,
        "time_factor": time_factor,
        "area_factor": area_factor,
        "weather_factor": round(weather_factor, 2),
        "weather_description": weather_desc,
    }
