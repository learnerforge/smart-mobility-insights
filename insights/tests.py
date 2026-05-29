import json
import math
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import CongestionLog, FASTagTransaction, NationalHighway, RoadCondition, TollCollection, TollPlaza, Trip
from .road_conditions import _haversine as rc_haversine, get_road_condition_factor, report_condition, resolve_condition
from .toll_calc import _haversine as tc_haversine, compute_fastag_toll, compute_toll, get_vehicle_multiplier
from .traffic import _haversine as tr_haversine, get_area_factor, get_congestion_level, get_time_factor
from .utils import load_config


class HaversineTests(TestCase):
    def test_same_point(self):
        for f in [rc_haversine, tc_haversine, tr_haversine]:
            assert f(0, 0, 0, 0) == 0.0, f"{f.__module__} same point failed"

    def test_known_distance(self):
        hyb_lat, hyb_lng = 17.4435, 78.3772
        del_lat, del_lng = 28.7041, 77.1025
        dist = tc_haversine(hyb_lat, hyb_lng, del_lat, del_lng)
        assert 1250 < dist < 1300, f"Hyderabad-Delhi distance {dist} out of range"

    def test_symmetry(self):
        d1 = tc_haversine(12.97, 77.59, 13.08, 80.27)
        d2 = tc_haversine(13.08, 80.27, 12.97, 77.59)
        assert abs(d1 - d2) < 0.001, f"Haversine not symmetric: {d1} vs {d2}"


class TollCalcTests(TestCase):
    def setUp(self):
        self.plaza = TollPlaza.objects.create(
            plaza_id="TEST001", name="Test Plaza", state="Telangana",
            latitude=17.44, longitude=78.37, plaza_type="National",
        )
        FASTagTransaction.objects.create(
            plaza=self.plaza, fiscal_year="2024-25", month="Apr",
            vehicle_count=1000, amount_collected=50000,
        )

    def test_compute_toll_slab_car(self):
        toll, model = compute_toll(8, "car")
        assert toll == 20.0, f"Expected 20, got {toll}"
        assert model == "slab", f"Expected slab, got {model}"

    def test_compute_toll_dynamic_bike(self):
        toll, model = compute_toll(25, "bike")
        expected = round(25 * 2.0 * 0.5, 2)
        assert toll == expected, f"Expected {expected}, got {toll}"
        assert model == "dynamic"

    def test_compute_toll_ambulance_free(self):
        toll, model = compute_toll(15, "ambulance")
        assert toll == 0.0

    def test_compute_toll_negative(self):
        toll, model = compute_toll(-5, "car")
        assert toll is None

    def test_fastag_toll(self):
        geom = {"type": "LineString", "coordinates": [[78.37, 17.44], [78.38, 17.45]]}
        total, model, plazas = compute_fastag_toll(geom, "car", fallback_distance=10)
        if total is not None:
            assert model == "fastag"
            assert len(plazas) > 0

    def test_fastag_toll_no_plazas(self):
        geom = {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}
        total, model, plazas = compute_fastag_toll(geom, "car", fallback_distance=10)
        if total is not None:
            assert model in ("slab", "dynamic")

    def test_get_vehicle_multiplier(self):
        assert get_vehicle_multiplier("car") == 1.0
        assert get_vehicle_multiplier("bike") == 0.5
        assert get_vehicle_multiplier("ambulance") == 0.0
        assert get_vehicle_multiplier("unknown") == 1.0


class TripModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", "test@test.com", "testpass")
        self.trip = Trip.objects.create(
            user=self.user, origin_name="Mumbai", dest_name="Pune",
            origin_lat=19.076, origin_lng=72.877, dest_lat=18.520, dest_lng=73.856,
            distance_km=150, duration_sec=7200, route_geometry={"type": "LineString", "coordinates": [[72.877, 19.076], [73.856, 18.520]]},
            vehicle_type="car", toll_amount=Decimal("300.00"), pricing_model="dynamic",
            congestion_level="moderate",
        )

    def test_trip_creation(self):
        assert Trip.objects.count() == 1

    def test_trip_str(self):
        assert "Mumbai" in str(self.trip)
        assert "Pune" in str(self.trip)

    def test_trip_clean_negative_distance(self):
        self.trip.distance_km = -1
        from django.core.exceptions import ValidationError
        try:
            self.trip.clean()
            assert False, "Should raise ValidationError"
        except ValidationError:
            pass

    def test_toll_collection(self):
        TollCollection.objects.create(
            trip=self.trip, base_toll=Decimal("200.00"),
            multiplier=Decimal("1.0"), total_toll=Decimal("200.00"),
            pricing_model="dynamic",
        )
        assert self.trip.toll.total_toll == Decimal("200.00")

    def test_toll_collection_str(self):
        tc = TollCollection.objects.create(
            trip=self.trip, base_toll=Decimal("200.00"),
            multiplier=Decimal("1.0"), total_toll=Decimal("200.00"),
            pricing_model="dynamic",
        )
        assert "200" in str(tc)


class NationalHighwayTests(TestCase):
    def setUp(self):
        NationalHighway.objects.create(
            nh_number="NH 44", name="North-South Corridor",
            length_km=3745, geometry={"type": "LineString", "coordinates": [[77.0, 28.0], [78.0, 27.0]]},
        )

    def test_nh_creation(self):
        assert NationalHighway.objects.count() == 1

    def test_nh_str(self):
        nh = NationalHighway.objects.first()
        assert "NH 44" in str(nh)


class TrafficAreaFactorTests(TestCase):
    def setUp(self):
        self.congestion_logs = [
            {"location_name": "Jn 1", "lat": 17.4435, "lng": 78.3772, "level": 1.5},
            {"location_name": "Jn 2", "lat": 17.4440, "lng": 78.3780, "level": 1.6},
            {"location_name": "Jn 3", "lat": 17.4445, "lng": 78.3790, "level": 1.4},
            {"location_name": "Jn 4", "lat": 17.4450, "lng": 78.3800, "level": 1.7},
            {"location_name": "Jn 5", "lat": 17.4455, "lng": 78.3810, "level": 1.5},
            {"location_name": "Jn 6", "lat": 12.9716, "lng": 77.5946, "level": 1.6},
            {"location_name": "Jn 7", "lat": 12.9720, "lng": 77.5955, "level": 1.5},
            {"location_name": "Jn 8", "lat": 12.9725, "lng": 77.5970, "level": 1.7},
            {"location_name": "Jn 9", "lat": 12.9730, "lng": 77.5985, "level": 1.6},
            {"location_name": "Jn 10", "lat": 12.9735, "lng": 77.6000, "level": 1.4},
            {"location_name": "Jn 11", "lat": 12.9740, "lng": 77.6015, "level": 1.5},
            {"location_name": "Jn 12", "lat": 19.0689, "lng": 72.8700, "level": 1.7},
            {"location_name": "Jn 13", "lat": 19.0695, "lng": 72.8705, "level": 1.6},
            {"location_name": "Jn 14", "lat": 19.0700, "lng": 72.8710, "level": 1.5},
            {"location_name": "Jn 15", "lat": 19.0705, "lng": 72.8720, "level": 1.8},
            {"location_name": "Jn 16", "lat": 19.0710, "lng": 72.8730, "level": 1.4},
            {"location_name": "Jn 17", "lat": 19.0715, "lng": 72.8740, "level": 1.6},
        ]

    def test_area_factor_hyderabad(self):
        factor = get_area_factor(17.444, 78.377, 17.446, 78.381, self.congestion_logs)
        assert factor > 1.0, f"Expected > 1.0 for Hyderabad, got {factor}"

    def test_area_factor_bangalore(self):
        factor = get_area_factor(12.972, 77.595, 12.974, 77.601, self.congestion_logs)
        assert factor > 1.0, f"Expected > 1.0 for Bangalore, got {factor}"

    def test_area_factor_mumbai(self):
        factor = get_area_factor(19.069, 72.870, 19.071, 72.874, self.congestion_logs)
        assert factor > 1.0, f"Expected > 1.0 for Mumbai, got {factor}"

    def test_area_factor_remote(self):
        factor = get_area_factor(0, 0, 0.01, 0.01, self.congestion_logs)
        assert factor == 1.0, f"Expected 1.0 for remote area, got {factor}"

    def test_area_factor_no_data(self):
        factor = get_area_factor(17.44, 78.37, 17.45, 78.36, [])
        assert factor == 1.0, f"Expected 1.0 with no data, got {factor}"

    def test_congestion_level(self):
        config = load_config()
        level, icon = get_congestion_level(1.0, config)
        assert level == "light"
        level, icon = get_congestion_level(2.5, config)
        assert level == "congested"

    def test_time_factor(self):
        config = load_config()
        factor = get_time_factor(config)
        assert 0.5 < factor < 3.0, f"Time factor {factor} out of range"


class RoadConditionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("rcuser", "rc@test.com", "rcpass")

    def test_report_new_condition(self):
        rc, created = report_condition(
            "Test Road", 17.44, 78.37, "pothole", "medium", "Test pothole", self.user,
        )
        assert created
        assert rc.report_count == 1
        assert rc.status == "reported"

    def test_report_duplicate(self):
        rc1, _ = report_condition(
            "Road A", 17.44, 78.37, "pothole", "medium", "", self.user,
        )
        rc2, created = report_condition(
            "Road A", 17.44, 78.37, "pothole", "medium", "", self.user,
        )
        assert not created
        assert rc2.report_count == 2

    def test_auto_verify(self):
        rc, _ = report_condition(
            "Road B", 17.44, 78.37, "pothole", "low", "", self.user,
        )
        for _ in range(3):
            report_condition("Road B", 17.44, 78.37, "pothole", "low", "")
        rc.refresh_from_db()
        assert rc.status == "verified"

    def test_resolve_condition(self):
        rc, _ = report_condition(
            "Road C", 17.44, 78.37, "pothole", "medium", "", self.user,
        )
        resolved = resolve_condition(rc.id)
        assert resolved is not None
        assert resolved.status == "resolved"

    def test_resolve_nonexistent(self):
        resolved = resolve_condition(99999)
        assert resolved is None

    def test_road_condition_factor(self):
        report_condition("Close Road", 17.44, 78.37, "closed", "high", "", self.user)
        factor = get_road_condition_factor(17.44, 78.37, 17.45, 78.38)
        assert factor > 0, f"Expected factor > 0, got {factor}"

    def test_road_condition_factor_no_nearby(self):
        factor = get_road_condition_factor(0, 0, 0.01, 0.01)
        assert factor == 0.0, f"Expected 0.0, got {factor}"
