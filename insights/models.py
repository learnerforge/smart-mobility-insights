from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth.models import User


class Trip(models.Model):
    VEHICLE_CHOICES = [
        ("car", "Car"),
        ("bike", "Bike"),
        ("bus", "Bus"),
        ("truck", "Truck"),
        ("ambulance", "Ambulance"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trips", db_index=True)
    origin_name = models.CharField(max_length=255)
    dest_name = models.CharField(max_length=255)
    origin_lat = models.FloatField()
    origin_lng = models.FloatField()
    dest_lat = models.FloatField()
    dest_lng = models.FloatField()
    distance_km = models.FloatField(validators=[MinValueValidator(0)])
    duration_sec = models.FloatField(validators=[MinValueValidator(0)])
    route_geometry = models.JSONField()
    vehicle_type = models.CharField(max_length=50, choices=VEHICLE_CHOICES, default="car", db_index=True)
    toll_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pricing_model = models.CharField(max_length=20, null=True, blank=True)
    congestion_level = models.CharField(max_length=20, default="light")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Trip"
        verbose_name_plural = "Trips"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["vehicle_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.origin_name} → {self.dest_name} ({self.vehicle_type})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.distance_km is not None and self.distance_km < 0:
            raise ValidationError({"distance_km": "Distance cannot be negative."})
        if self.duration_sec is not None and self.duration_sec < 0:
            raise ValidationError({"duration_sec": "Duration cannot be negative."})


class TollCollection(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name="toll")
    base_toll = models.DecimalField(max_digits=12, decimal_places=2)
    multiplier = models.DecimalField(max_digits=5, decimal_places=2)
    total_toll = models.DecimalField(max_digits=12, decimal_places=2)
    pricing_model = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Toll Collection"
        verbose_name_plural = "Toll Collections"

    def __str__(self):
        return f"₹{self.total_toll} - {self.trip}"


class CongestionLog(models.Model):
    location_name = models.CharField(max_length=255, db_index=True)
    lat = models.FloatField()
    lng = models.FloatField()
    level = models.FloatField(default=1.0, validators=[MinValueValidator(0)])
    source = models.CharField(max_length=50, default="query")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Congestion Log"
        verbose_name_plural = "Congestion Logs"

    def __str__(self):
        return f"{self.location_name} ({self.level})"


class RoadCondition(models.Model):
    CONDITION_CHOICES = [
        ("good", "Good"),
        ("fair", "Fair"),
        ("poor", "Poor"),
        ("under_construction", "Under Construction"),
        ("closed", "Closed"),
        ("accident", "Accident"),
        ("flooding", "Flooding"),
        ("pothole", "Pothole"),
    ]
    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]
    STATUS_CHOICES = [
        ("reported", "Reported"),
        ("verified", "Verified"),
        ("resolved", "Resolved"),
    ]

    road_name = models.CharField(max_length=255)
    lat = models.FloatField()
    lng = models.FloatField()
    condition_type = models.CharField(max_length=30, choices=CONDITION_CHOICES, db_index=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="medium", db_index=True)
    description = models.TextField(blank=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    report_count = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="reported", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Road Condition"
        verbose_name_plural = "Road Conditions"
        indexes = [
            models.Index(fields=["status", "condition_type"]),
            models.Index(fields=["lat", "lng"]),
        ]

    def __str__(self):
        return f"{self.get_condition_type_display()} on {self.road_name} ({self.get_status_display()})"


class TollPlaza(models.Model):
    PLAZA_TYPE_CHOICES = [
        ("National", "National"),
        ("State", "State"),
    ]
    plaza_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    state = models.CharField(max_length=100, db_index=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    plaza_type = models.CharField(max_length=50, choices=PLAZA_TYPE_CHOICES, default="National")

    class Meta:
        verbose_name = "Toll Plaza"
        verbose_name_plural = "Toll Plazas"
        indexes = [
            models.Index(fields=["state", "plaza_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.state})"


class FASTagTransaction(models.Model):
    plaza = models.ForeignKey(TollPlaza, on_delete=models.CASCADE, related_name="transactions")
    fiscal_year = models.CharField(max_length=20, db_index=True)
    month = models.CharField(max_length=20)
    vehicle_count = models.BigIntegerField()
    amount_collected = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = "FASTag Transaction"
        verbose_name_plural = "FASTag Transactions"
        indexes = [
            models.Index(fields=["plaza", "fiscal_year"]),
        ]

    def __str__(self):
        return f"{self.plaza.name} ({self.fiscal_year} {self.month})"


class NationalHighway(models.Model):
    nh_number = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=255, blank=True)
    length_km = models.FloatField(null=True, blank=True)
    geometry = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "National Highway"
        verbose_name_plural = "National Highways"
        indexes = [
            models.Index(fields=["nh_number"]),
        ]

    def __str__(self):
        return f"NH {self.nh_number}"


class RoadAccident(models.Model):
    year = models.IntegerField(db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    type_of_traffic_violation = models.CharField(max_length=100, null=True, blank=True)
    category = models.CharField(max_length=50)
    value = models.IntegerField()
    source = models.CharField(max_length=50, default="MoRTH")

    class Meta:
        verbose_name = "Road Accident"
        verbose_name_plural = "Road Accidents"
        indexes = [
            models.Index(fields=["year", "state"]),
        ]

    def __str__(self):
        return f"{self.state} {self.year} {self.category}: {self.value}"


class RoadAccidentByCollision(models.Model):
    year = models.IntegerField(db_index=True)
    collision_type = models.CharField(max_length=100)
    accidents = models.IntegerField(null=True)
    killed = models.IntegerField(null=True)
    injured = models.IntegerField(null=True)

    class Meta:
        verbose_name = "Road Accident (Collision Type)"
        verbose_name_plural = "Road Accidents (Collision Types)"

    def __str__(self):
        return f"{self.year} {self.collision_type}"


class RoadAccidentByRoadUser(models.Model):
    year = models.IntegerField(db_index=True)
    road_user_type = models.CharField(max_length=100)
    killed = models.IntegerField(null=True)

    class Meta:
        verbose_name = "Road Accident (Road User)"
        verbose_name_plural = "Road Accidents (Road Users)"

    def __str__(self):
        return f"{self.year} {self.road_user_type}"


class RoadStatistic(models.Model):
    year = models.IntegerField(db_index=True)
    road_category = models.CharField(max_length=100)
    road_property = models.CharField(max_length=50)
    value = models.FloatField()
    unit = models.CharField(max_length=50, default="value in Kilometer")

    class Meta:
        verbose_name = "Road Statistic"
        verbose_name_plural = "Road Statistics"
        indexes = [
            models.Index(fields=["year", "road_category"]),
        ]

    def __str__(self):
        return f"{self.year} {self.road_category} ({self.road_property})"


class NETCProcessingRate(models.Model):
    toll_plaza_id = models.CharField(max_length=50, db_index=True)
    plaza_name = models.CharField(max_length=255)
    plaza_type = models.CharField(max_length=50)
    fiscal_year = models.CharField(max_length=20)
    month = models.CharField(max_length=20)
    pct_within_2min = models.FloatField()

    class Meta:
        verbose_name = "NETC Processing Rate"
        verbose_name_plural = "NETC Processing Rates"
        indexes = [
            models.Index(fields=["toll_plaza_id", "fiscal_year"]),
        ]

    def __str__(self):
        return f"{self.plaza_name} ({self.fiscal_year} {self.month})"


class NETCUptime(models.Model):
    fiscal_year = models.CharField(max_length=20, db_index=True)
    month = models.CharField(max_length=20)
    uptime_pct = models.FloatField()
    incidents = models.IntegerField()
    downtime_minutes = models.IntegerField()

    class Meta:
        verbose_name = "NETC Uptime"
        verbose_name_plural = "NETC Uptimes"

    def __str__(self):
        return f"{self.fiscal_year} {self.month}: {self.uptime_pct}%"


class NETCDispute(models.Model):
    fiscal_year = models.CharField(max_length=20, db_index=True)
    month = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    value = models.FloatField()

    class Meta:
        verbose_name = "NETC Dispute"
        verbose_name_plural = "NETC Disputes"

    def __str__(self):
        return f"{self.bank_name} {self.category} ({self.fiscal_year} {self.month})"


class EconomicSurvey(models.Model):
    year = models.IntegerField(unique=True)
    total_road_km = models.FloatField(null=True, blank=True)
    surfaced_road_km = models.FloatField(null=True, blank=True)
    nh_km = models.FloatField(null=True, blank=True)
    sh_km = models.FloatField(null=True, blank=True)
    registered_vehicles = models.BigIntegerField(null=True, blank=True)
    revenue_central = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    revenue_state = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Economic Survey"
        verbose_name_plural = "Economic Surveys"

    def __str__(self):
        return f"Economic Survey {self.year}"
