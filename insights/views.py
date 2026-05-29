import json
import logging
import time
from datetime import datetime, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Sum
from django.db.utils import IntegrityError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST

from .forms import LoginForm, RegisterForm
from .models import CongestionLog, RoadCondition, TollCollection, Trip
from .road_conditions import _haversine, get_road_condition_factor, report_condition, resolve_condition
from .routing import geocode, get_routes
from .toll_calc import compute_fastag_toll, get_vehicle_multiplier
from .traffic import get_traffic_info
logger = logging.getLogger(__name__)

_LOGIN_RATE_MAP = {}


def _check_login_rate(ip):
    now = time.time()
    window = 60
    max_attempts = 10
    if ip in _LOGIN_RATE_MAP:
        attempts, first = _LOGIN_RATE_MAP[ip]
        if now - first > window:
            _LOGIN_RATE_MAP[ip] = (1, now)
            return True
        if attempts >= max_attempts:
            return False
        _LOGIN_RATE_MAP[ip] = (attempts + 1, first)
    else:
        _LOGIN_RATE_MAP[ip] = (1, now)
    return True


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR", "")
        if not _check_login_rate(ip):
            logger.warning("Login rate limit hit for IP: %s", ip)
            return render(request, "registration/login.html", {
                "form": LoginForm(),
                "error": "Too many login attempts. Try again later.",
            })
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user:
                login(request, user)
                logger.info("User logged in: %s", user.username)
                return redirect("/")
            logger.warning("Login failed: invalid credentials for '%s'", form.cleaned_data["username"])
            return render(request, "registration/login.html", {
                "form": form,
                "error": "Invalid username or password.",
            })
        return render(request, "registration/login.html", {
            "form": form,
            "error": "Please correct the errors below.",
        })
    else:
        form = LoginForm()
    return render(request, "registration/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.create_user(
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                )
            except IntegrityError:
                logger.warning("Duplicate username (race): %s", form.cleaned_data["username"])
                form.add_error("username", "Username already taken. Please choose another.")
                return render(request, "registration/register.html", {"form": form})
            login(request, user)
            logger.info("User registered: %s", user.username)
            return redirect("/")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("/login/")


@login_required
@ensure_csrf_cookie
def map_view(request):
    return render(request, "index.html")

@login_required
def api_geocode(request):
    q = request.GET.get("q", "")
    if not q:
        return JsonResponse({"error": "Missing query"}, status=400)
    try:
        results = geocode(q)
        data = [
            {"lat": float(r["lat"]), "lng": float(r["lon"]), "display_name": r["display_name"]}
            for r in results
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        logger.exception("Geocode failed for query: %s", q)
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_POST
def api_route(request):
    try:
        body = json.loads(request.body)
        origin_lat = body["origin_lat"]
        origin_lng = body["origin_lng"]
        dest_lat = body["dest_lat"]
        dest_lng = body["dest_lng"]
        origin_name = body.get("origin_name", "")
        dest_name = body.get("dest_name", "")
        vehicle = body.get("vehicle", "car")

        osrm_data = get_routes(origin_lat, origin_lng, dest_lat, dest_lng)
        congestion_logs = list(CongestionLog.objects.all().values("location_name", "lat", "lng"))
        traffic = get_traffic_info(
            origin_name, dest_name, congestion_logs,
            origin_lat=origin_lat, origin_lng=origin_lng,
            dest_lat=dest_lat, dest_lng=dest_lng,
        )

        road_factor = get_road_condition_factor(
            origin_lat, origin_lng, dest_lat, dest_lng
        )
        combined_factor = max(round(traffic["factor"] + road_factor, 2), 0.5)

        routes = []
        for i, route in enumerate(osrm_data.get("routes", [])):
            distance_km = round(route["legs"][0]["distance"] / 1000, 1)
            duration_sec = route["legs"][0]["duration"]
            adjusted_duration = int(duration_sec * combined_factor)
            toll, pricing_model, plaza_breakdown = compute_fastag_toll(
                route["geometry"], vehicle, fallback_distance=distance_km
            )

            routes.append(
                {
                    "index": i,
                    "recommended": False,
                    "distance_km": distance_km,
                    "duration_sec": duration_sec,
                    "adjusted_duration_sec": adjusted_duration,
                    "adjusted_duration_min": round(adjusted_duration / 60, 1),
                    "toll": float(toll) if toll is not None else None,
                    "pricing_model": pricing_model,
                    "traffic": traffic,
                    "road_condition_factor": road_factor,
                    "geometry": route["geometry"],
                    "toll_plazas": plaza_breakdown,
                }
            )

        if routes:
            # Determine fastest, cheapest, and best overall
            min_time = min(r["adjusted_duration_min"] for r in routes)
            valid_tolls = [r["toll"] for r in routes if r["toll"] is not None]
            min_toll = min(valid_tolls) if valid_tolls else None

            for r in routes:
                tags = []
                if r["adjusted_duration_min"] == min_time:
                    tags.append("Fastest")
                if min_toll is not None and r["toll"] == min_toll:
                    tags.append("Cheapest")
                r["tags"] = tags

            # Best overall: lowest composite score (normalized time + normalized toll)
            t_min, t_max = min_time, max(r["adjusted_duration_min"] for r in routes)
            t_range = t_max - t_min if t_max > t_min else 1
            if min_toll is not None and any(r["toll"] is not None for r in routes):
                tolls = [r["toll"] for r in routes if r["toll"] is not None]
                c_min, c_max = min(tolls), max(tolls)
                c_range = c_max - c_min if c_max > c_min else 1
            else:
                c_min, c_max, c_range = 0, 0, 1

            best_score = float("inf")
            for r in routes:
                t_score = (r["adjusted_duration_min"] - t_min) / t_range
                c_score = ((r["toll"] or 0) - c_min) / c_range if min_toll is not None else 0
                r["score"] = round(t_score + c_score, 3)
                if r["score"] < best_score:
                    best_score = r["score"]

            for r in routes:
                if r["score"] == best_score:
                    r["recommended"] = True
                    r["tags"].append("Best")

        if routes:
            r = routes[0]
            trip = Trip.objects.create(
                user=request.user,
                origin_name=origin_name,
                dest_name=dest_name,
                origin_lat=origin_lat,
                origin_lng=origin_lng,
                dest_lat=dest_lat,
                dest_lng=dest_lng,
                distance_km=r["distance_km"],
                duration_sec=r["adjusted_duration_sec"],
                route_geometry=r["geometry"],
                vehicle_type=vehicle,
                toll_amount=r["toll"],
                pricing_model=r["pricing_model"],
                congestion_level=r["traffic"]["level"],
            )

            multiplier = get_vehicle_multiplier(vehicle)
            if r["toll"] is not None and multiplier > 0:
                base_toll = round(r["toll"] / multiplier, 2)
                TollCollection.objects.create(
                    trip=trip,
                    base_toll=base_toll,
                    multiplier=multiplier,
                    total_toll=r["toll"],
                    pricing_model=r["pricing_model"],
                )

            for name, lat, lng in [(origin_name, origin_lat, origin_lng), (dest_name, dest_lat, dest_lng)]:
                existing = CongestionLog.objects.filter(
                    location_name=name, lat=lat, lng=lng,
                ).first()
                if not existing:
                    CongestionLog.objects.create(
                        location_name=name,
                        lat=lat,
                        lng=lng,
                        level=traffic["factor"],
                        source="query",
                    )

        return JsonResponse({"routes": routes, "traffic": traffic})
    except Exception as e:
        logger.exception("Route planning failed for user %s", request.user.username)
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def api_trips(request):
    page = max(int(request.GET.get("page", 1)), 1)
    per_page = min(int(request.GET.get("per_page", 100)), 500)
    offset = (page - 1) * per_page
    trips = Trip.objects.filter(user=request.user).values(
        "id", "origin_name", "dest_name", "distance_km", "toll_amount",
        "vehicle_type", "created_at",
    ).order_by("-created_at")[offset:offset + per_page]
    total = Trip.objects.filter(user=request.user).count()
    return JsonResponse({
        "data": list(trips),
        "page": page,
        "per_page": per_page,
        "total": total,
    }, safe=False)


@staff_member_required
def api_admin_stats(request):
    all_trips = Trip.objects.all()
    total = all_trips.aggregate(Sum("toll_amount"))["toll_amount__sum"] or 0
    count = all_trips.count()
    avg_toll = all_trips.aggregate(Avg("toll_amount"))["toll_amount__avg"] or 0

    today = datetime.now().date()
    daily_data = []
    for i in range(30):
        day = today - timedelta(days=29 - i)
        day_total = (
            all_trips.filter(created_at__date=day).aggregate(Sum("toll_amount"))["toll_amount__sum"] or 0
        )
        daily_data.append({"date": day.isoformat(), "revenue": float(day_total)})

    vehicle_data = list(all_trips.values("vehicle_type").annotate(count=Count("id"), total=Sum("toll_amount")))

    return JsonResponse(
        {
            "total_revenue": float(total),
            "total_trips": count,
            "avg_toll": float(avg_toll),
            "daily_revenue": daily_data,
            "vehicle_breakdown": vehicle_data,
        }
    )


@login_required
def api_road_conditions(request):
    qs = RoadCondition.objects.all()
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius")
    if lat and lng and radius:
        try:
            clat, clng, r = float(lat), float(lng), float(radius)
            ids = []
            for rc in qs:
                if _haversine(clat, clng, rc.lat, rc.lng) <= r:
                    ids.append(rc.id)
            qs = qs.filter(id__in=ids)
        except ValueError:
            pass
    data = list(qs.values(
        "id", "road_name", "lat", "lng", "condition_type", "severity",
        "description", "report_count", "status", "created_at",
    )[:500])
    return JsonResponse(data, safe=False)


@login_required
@require_POST
def api_report_road_condition(request):
    try:
        body = json.loads(request.body)
        rc, created = report_condition(
            road_name=body["road_name"],
            lat=float(body["lat"]),
            lng=float(body["lng"]),
            condition_type=body["condition_type"],
            severity=body.get("severity", "medium"),
            description=body.get("description", ""),
            user=request.user,
        )
        return JsonResponse({
            "id": rc.id,
            "status": rc.status,
            "report_count": rc.report_count,
            "created": created,
        })
    except Exception as e:
        logger.exception("Road condition report failed for user %s", request.user.username)
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
@require_POST
def api_resolve_road_condition(request, condition_id):
    rc = resolve_condition(condition_id)
    if rc:
        return JsonResponse({"id": rc.id, "status": rc.status})
    return JsonResponse({"error": "Not found or already resolved"}, status=404)


@staff_member_required
def api_road_condition_stats(request):
    total = RoadCondition.objects.count()
    open_count = RoadCondition.objects.filter(status__in=["reported", "verified"]).count()
    resolved_count = RoadCondition.objects.filter(status="resolved").count()
    type_breakdown = list(
        RoadCondition.objects.values("condition_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    severity_breakdown = list(
        RoadCondition.objects.values("severity")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    return JsonResponse({
        "total": total,
        "open": open_count,
        "resolved": resolved_count,
        "type_breakdown": type_breakdown,
        "severity_breakdown": severity_breakdown,
    })


@login_required
def api_reverse_geocode(request):
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    if not lat or not lng:
        return JsonResponse({"error": "Missing lat/lng"}, status=400)
    try:
        from .routing import reverse_geocode
        result = reverse_geocode(float(lat), float(lng))
        display_name = result.get("display_name", f"{lat}, {lng}")
        return JsonResponse({"display_name": display_name})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def health_check(request):
    return JsonResponse({"status": "ok"})


@login_required
def api_fastag_stats(request):
    from .models import FASTagTransaction
    year = request.GET.get("year")
    state = request.GET.get("state")
    qs = FASTagTransaction.objects.select_related("plaza")
    if year:
        qs = qs.filter(fiscal_year=year)
    if state:
        qs = qs.filter(plaza__state=state)
    total_volume = qs.aggregate(Sum("vehicle_count"))["vehicle_count__sum"] or 0
    total_amount = qs.aggregate(Sum("amount_collected"))["amount_collected__sum"] or 0
    state_breakdown = list(
        qs.values("plaza__state").annotate(
            volume=Sum("vehicle_count"),
            amount=Sum("amount_collected"),
        ).order_by("-volume")
    )
    return JsonResponse({
        "total_volume": total_volume,
        "total_amount": float(total_amount),
        "state_breakdown": state_breakdown,
    })


@login_required
def api_toll_plazas(request):
    from .models import TollPlaza, FASTagTransaction
    from django.db.models import Avg, Sum
    state = request.GET.get("state")
    qs = TollPlaza.objects.all()
    if state:
        qs = qs.filter(state=state)
    data = list(qs.values("id", "name", "state", "latitude", "longitude", "plaza_type"))
    # Enrich with average toll per vehicle from FASTag transactions
    plaza_ids = [p["id"] for p in data]
    if plaza_ids:
        aggs = FASTagTransaction.objects.filter(plaza_id__in=plaza_ids).values("plaza_id").annotate(
            total_amount=Sum("amount_collected"),
            total_vehicles=Sum("vehicle_count"),
        )
        agg_map = {}
        for a in aggs:
            tid = a["plaza_id"]
            tv = a["total_vehicles"]
            agg_map[tid] = {
                "avg_toll": float(a["total_amount"]) / tv if tv else None,
                "total_vehicles": tv,
            }
        for p in data:
            info = agg_map.get(p["id"], {})
            p["avg_toll"] = info.get("avg_toll")
            p["total_vehicles"] = info.get("total_vehicles")
    return JsonResponse(data, safe=False)


def _clean_nh(nh_raw):
    nh = nh_raw.strip()
    nh = nh.replace("  ", " ")
    nh = nh.replace("`", "").replace(",", "").replace(";", ",")
    nh = nh.replace("(G.Q)", "").strip()
    nh = nh.replace("  ", " ")
    return nh


def api_national_highways(request):
    import re
    from collections import OrderedDict
    from .models import NationalHighway

    def _simplify(coords, epsilon=0.001):
        if len(coords) <= 2:
            return coords
        def _perp_dist(p, a, b):
            lng0, lat0 = p; lng1, lat1 = a; lng2, lat2 = b
            num = abs((lat2 - lat1) * lng0 - (lng2 - lng1) * lat0 + lng2 * lat1 - lat2 * lng1)
            den = ((lat2 - lat1) ** 2 + (lng2 - lng1) ** 2) ** 0.5
            return num / den if den else 0
        def _rdp(pts):
            if len(pts) <= 2: return pts
            dmax = 0; idx = 0
            for i in range(1, len(pts) - 1):
                d = _perp_dist(pts[i], pts[0], pts[-1])
                if d > dmax: dmax = d; idx = i
            if dmax > epsilon:
                left = _rdp(pts[:idx + 1]); right = _rdp(pts[idx:])
                return left[:-1] + right
            return [pts[0], pts[-1]]
        return _rdp(coords)

    nh = request.GET.get("nh")
    qs = NationalHighway.objects.all()
    if nh:
        cleaned_search = nh.replace("  ", " ").replace("`", "").replace(",", "").strip()
        qs = qs.filter(nh_number__icontains=cleaned_search)
    merged = OrderedDict()
    for obj in qs.iterator():
        key = obj.nh_number
        if key not in merged:
            merged[key] = {"nh_number": obj.nh_number, "name": obj.name, "length_km": obj.length_km, "geometries": []}
        merged[key]["geometries"].append(obj.geometry)
    result = []
    for key, entry in merged.items():
        geoms = entry["geometries"]
        cleaned = _clean_nh(entry["nh_number"])
        simplified = []
        for g in geoms:
            coords = g.get("coordinates", [])
            if coords:
                simplified.append(_simplify(coords, epsilon=0.001))
        if len(simplified) == 1:
            entry["geometry"] = {"type": "LineString", "coordinates": simplified[0]}
        else:
            entry["geometry"] = {"type": "MultiLineString", "coordinates": simplified}
        entry["nh_number"] = cleaned
        del entry["geometries"]
        result.append(entry)
    return JsonResponse(result, safe=False)


@login_required
def api_road_accident_stats(request):
    from .models import RoadAccident
    year = request.GET.get("year")
    qs = RoadAccident.objects.all()
    if year:
        qs = qs.filter(year=int(year))
    total = qs.aggregate(Sum("value"))["value__sum"] or 0
    by_state = list(
        qs.values("state").annotate(
            total=Sum("value"),
            count=Count("id"),
        ).order_by("-total")[:20]
    )
    by_violation = list(
        qs.values("type_of_traffic_violation").annotate(
            total=Sum("value"),
        ).order_by("-total")
    )
    return JsonResponse({
        "total": total,
        "by_state": by_state,
        "by_violation": by_violation,
    })


@login_required
def api_road_statistics(request):
    from .models import RoadStatistic
    year = request.GET.get("year")
    qs = RoadStatistic.objects.all()
    if year:
        qs = qs.filter(year=int(year))
    years = list(qs.values("year").distinct().order_by("-year").values_list("year", flat=True)[:20])
    by_year = []
    for y in years:
        yr_qs = qs.filter(year=y)
        total = yr_qs.filter(road_property="Total").aggregate(Sum("value"))["value__sum"]
        surfaced = yr_qs.filter(road_property="Surfaced").aggregate(Sum("value"))["value__sum"]
        by_year.append({"year": y, "total_km": total or 0, "surfaced_km": surfaced or 0})
    by_category = list(
        qs.filter(road_property="Total").values("road_category").annotate(
            total=Sum("value")
        ).order_by("-total")
    )
    return JsonResponse({"by_year": by_year, "by_category": by_category})


@login_required
def api_netc_stats(request):
    from .models import NETCUptime, NETCProcessingRate, NETCDispute
    uptime_data = list(NETCUptime.objects.all().order_by("fiscal_year", "month")[:60])
    processing_data = list(
        NETCProcessingRate.objects.values("fiscal_year").annotate(
            avg_rate=Avg("pct_within_2min")
        ).order_by("-fiscal_year")[:10]
    )
    dispute_totals = list(
        NETCDispute.objects.values("category").annotate(
            total=Sum("value")
        ).order_by("-total")
    )
    return JsonResponse({
        "uptime": [{"period": f"{u.fiscal_year} {u.month}", "uptime": u.uptime_pct, "downtime": u.downtime_minutes} for u in uptime_data],
        "avg_processing_rate": processing_data,
        "dispute_totals": dispute_totals,
    })


@login_required
def api_economic_survey(request):
    from .models import EconomicSurvey
    data = list(EconomicSurvey.objects.all().order_by("year").values())
    return JsonResponse(data, safe=False)


@login_required
def api_road_collision_stats(request):
    from .models import RoadAccidentByCollision
    year = request.GET.get("year")
    qs = RoadAccidentByCollision.objects.all()
    if year:
        qs = qs.filter(year=int(year))
    data = list(qs.values().order_by("-year", "collision_type"))
    totals = qs.aggregate(
        total_accidents=Sum("accidents"),
        total_killed=Sum("killed"),
        total_injured=Sum("injured"),
    )
    return JsonResponse({"data": data, "totals": totals})


@login_required
def api_road_user_stats(request):
    from .models import RoadAccidentByRoadUser
    year = request.GET.get("year")
    qs = RoadAccidentByRoadUser.objects.all()
    if year:
        qs = qs.filter(year=int(year))
    data = list(qs.values().order_by("-year", "-killed"))
    return JsonResponse(data, safe=False)


@login_required
def api_netc_disputes(request):
    from .models import NETCDispute
    year = request.GET.get("year")
    qs = NETCDispute.objects.all()
    if year:
        qs = qs.filter(fiscal_year=year)
    data = list(qs.values().order_by("fiscal_year", "bank_name"))
    return JsonResponse(data, safe=False)
