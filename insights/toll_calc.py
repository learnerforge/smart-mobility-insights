import math

from django.db.models import Sum

from .models import FASTagTransaction, TollPlaza
from .utils import load_config

TOLL_PLAZA_SEARCH_RADIUS_KM = 8.0
DEDUP_RADIUS_KM = 2.0


def _haversine(lat1, lng1, lat2, lng2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_toll(distance_km, vehicle_type):
    if distance_km is None or distance_km < 0:
        return None, None

    config = load_config()
    tc = config["toll"]

    if distance_km <= tc["decision_threshold_km"]:
        pricing_model = "slab"
        base_toll = tc["slabs"][-1]["rate"]
        for slab in tc["slabs"]:
            if slab["max_km"] is None or distance_km <= slab["max_km"]:
                base_toll = slab["rate"]
                break
    else:
        pricing_model = "dynamic"
        base_toll = distance_km * tc["dynamic_rate_per_km"]

    vehicle = vehicle_type.lower()
    multiplier = tc["vehicle_multipliers"].get(vehicle, 1.0)
    final_toll = round(base_toll * multiplier, 2)
    return final_toll, pricing_model


def compute_fastag_toll(geometry, vehicle_type, fallback_distance=None):
    """
    Compute toll using FASTag historical data with distance-weighted matching.

    For each sampled point along the route, finds nearby toll plazas within
    search radius. Each plaza's avg_toll is weighted by proximity (closer = more).
    Nearby plazas within dedup radius are merged to avoid double-counting.
    The result is the sum of weighted tolls across all unique plazas, scaled
    by vehicle multiplier.

    Returns (total_toll, pricing_model, plaza_breakdown).
    Falls back to flat formula if no plazas found near route.
    """
    config = load_config()
    multiplier = config["toll"]["vehicle_multipliers"].get(vehicle_type.lower(), 1.0)

    coords = geometry.get("coordinates", []) if isinstance(geometry, dict) else []
    if not coords:
        return _fallback_toll(fallback_distance, multiplier)

    # Sample route points (every ~10 km, minimum 10 samples)
    step = max(1, len(coords) // 10)
    sampled = coords[::step]
    if sampled[-1] != coords[-1]:
        sampled.append(coords[-1])

    # Pre-compute plaza averages
    plaza_avgs = {}
    qs = FASTagTransaction.objects.values("plaza_id").annotate(
        total_vehicles=Sum("vehicle_count"),
        total_amount=Sum("amount_collected"),
    )
    for row in qs:
        if row["total_vehicles"] and row["total_vehicles"] > 0:
            plaza_avgs[row["plaza_id"]] = float(row["total_amount"]) / row["total_vehicles"]

    all_plazas = list(TollPlaza.objects.all().values(
        "id", "name", "state", "latitude", "longitude"
    ))

    # Step 1: Find all plaza matches with distances
    match_scores = {}
    for plaza in all_plazas:
        min_dist = float("inf")
        for lng, lat in sampled:
            dist = _haversine(plaza["latitude"], plaza["longitude"], lat, lng)
            if dist < min_dist:
                min_dist = dist
        if min_dist <= TOLL_PLAZA_SEARCH_RADIUS_KM:
            avg = plaza_avgs.get(plaza["id"])
            if avg is not None:
                # Weight: linear decay from 1.0 at 0 km to 0.3 at search radius
                weight = max(0.3, 1.0 - (min_dist / TOLL_PLAZA_SEARCH_RADIUS_KM) * 0.7)
                match_scores[plaza["id"]] = {
                    "name": plaza["name"],
                    "state": plaza["state"],
                    "avg_toll": avg,
                    "weight": round(weight, 3),
                    "min_dist": round(min_dist, 2),
                }

    if not match_scores:
        return _fallback_toll(fallback_distance, multiplier)

    # Step 2: De-duplicate plazas within DEDUP_RADIUS_KM of each other
    plaza_ids = list(match_scores.keys())
    dedup_groups = []
    assigned = set()

    for pid in plaza_ids:
        if pid in assigned:
            continue
        p = next(p for p in all_plazas if p["id"] == pid)
        group = [pid]
        assigned.add(pid)
        for other_id in plaza_ids:
            if other_id in assigned:
                continue
            o = next(p for p in all_plazas if p["id"] == other_id)
            d = _haversine(p["latitude"], p["longitude"], o["latitude"], o["longitude"])
            if d <= DEDUP_RADIUS_KM:
                group.append(other_id)
                assigned.add(other_id)

        dedup_groups.append(group)

    # Step 3: For each dedup group, keep the closest/most-weighted plaza
    final_plazas = []
    for group in dedup_groups:
        best = max(group, key=lambda pid: match_scores[pid]["weight"])
        info = match_scores[best]
        weighted_toll = round(info["avg_toll"] * multiplier * info["weight"], 2)
        final_plazas.append({
            "name": info["name"],
            "state": info["state"],
            "avg_toll": weighted_toll,
            "distance_km": info["min_dist"],
        })

    # Step 4: Sort by route order (closest to start, approximated by min_dist)
    final_plazas.sort(key=lambda p: p["distance_km"])
    total = round(sum(p["avg_toll"] for p in final_plazas), 2)
    return total, "fastag", final_plazas


def _fallback_toll(distance, multiplier):
    if distance is None or distance < 0:
        return None, None, []
    config = load_config()
    tc = config["toll"]
    if distance <= tc["decision_threshold_km"]:
        base = tc["slabs"][-1]["rate"]
        for slab in tc["slabs"]:
            if slab["max_km"] is None or distance <= slab["max_km"]:
                base = slab["rate"]
                break
        pricing = "slab"
    else:
        base = distance * tc["dynamic_rate_per_km"]
        pricing = "dynamic"
    return round(base * multiplier, 2), pricing, []


def get_vehicle_multiplier(vehicle_type):
    config = load_config()
    return config["toll"]["vehicle_multipliers"].get(vehicle_type.lower(), 1.0)
