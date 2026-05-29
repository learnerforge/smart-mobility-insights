import logging
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


def get_area_factor(origin_name, dest_name, congestion_logs):
    origin_lower = origin_name.lower() if origin_name else ""
    dest_lower = dest_name.lower() if dest_name else ""
    count = 0
    for log in congestion_logs:
        log_name = log.get("location_name", "").lower()
        if origin_lower and origin_lower in log_name:
            count += 1
        if dest_lower and dest_lower in log_name:
            count += 1
    if count > 20:
        return 2.0
    elif count > 10:
        return 1.5
    elif count > 5:
        return 1.2
    return 1.0


def get_traffic_info(
    origin_name, dest_name, congestion_logs=None,
    origin_lat=None, origin_lng=None, dest_lat=None, dest_lng=None,
):
    config = load_config()
    time_factor = get_time_factor(config)
    area_factor = get_area_factor(origin_name, dest_name, congestion_logs or [])
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
