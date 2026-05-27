from django.contrib import admin
from .models import (
    Trip, TollCollection, CongestionLog, RoadCondition,
    TollPlaza, FASTagTransaction, NationalHighway,
    RoadAccident, RoadAccidentByCollision, RoadAccidentByRoadUser,
    RoadStatistic, NETCProcessingRate, NETCUptime, NETCDispute,
    EconomicSurvey,
)


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['user', 'origin_name', 'dest_name', 'distance_km', 'toll_amount', 'vehicle_type', 'created_at']
    list_filter = ['vehicle_type', 'congestion_level', 'created_at']
    search_fields = ['origin_name', 'dest_name', 'user__username']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']


@admin.register(TollCollection)
class TollCollectionAdmin(admin.ModelAdmin):
    list_display = ['trip', 'base_toll', 'multiplier', 'total_toll', 'pricing_model']
    list_filter = ['pricing_model']


@admin.register(CongestionLog)
class CongestionLogAdmin(admin.ModelAdmin):
    list_display = ['location_name', 'level', 'source', 'created_at']
    list_filter = ['source', 'created_at']
    readonly_fields = ['created_at']


@admin.register(RoadCondition)
class RoadConditionAdmin(admin.ModelAdmin):
    list_display = ['road_name', 'condition_type', 'severity', 'status', 'report_count', 'created_at']
    list_filter = ['condition_type', 'severity', 'status']
    search_fields = ['road_name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TollPlaza)
class TollPlazaAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'plaza_type', 'latitude', 'longitude']
    list_filter = ['state', 'plaza_type']
    search_fields = ['name']


@admin.register(FASTagTransaction)
class FASTagTransactionAdmin(admin.ModelAdmin):
    list_display = ['plaza', 'fiscal_year', 'month', 'vehicle_count', 'amount_collected']
    list_filter = ['fiscal_year', 'month']
    search_fields = ['plaza__name']


@admin.register(NationalHighway)
class NationalHighwayAdmin(admin.ModelAdmin):
    list_display = ['nh_number', 'name', 'length_km']
    search_fields = ['nh_number', 'name']


@admin.register(RoadAccident)
class RoadAccidentAdmin(admin.ModelAdmin):
    list_display = ['state', 'year', 'category', 'value']
    list_filter = ['year', 'state']
    search_fields = ['state']


@admin.register(RoadAccidentByCollision)
class RoadAccidentByCollisionAdmin(admin.ModelAdmin):
    list_display = ['year', 'collision_type', 'accidents', 'killed', 'injured']
    list_filter = ['year']


@admin.register(RoadAccidentByRoadUser)
class RoadAccidentByRoadUserAdmin(admin.ModelAdmin):
    list_display = ['year', 'road_user_type', 'killed']
    list_filter = ['year']


@admin.register(RoadStatistic)
class RoadStatisticAdmin(admin.ModelAdmin):
    list_display = ['year', 'road_category', 'road_property', 'value']
    list_filter = ['year', 'road_category', 'road_property']


@admin.register(NETCProcessingRate)
class NETCProcessingRateAdmin(admin.ModelAdmin):
    list_display = ['plaza_name', 'fiscal_year', 'month', 'pct_within_2min']
    list_filter = ['fiscal_year', 'plaza_type']


@admin.register(NETCUptime)
class NETCUptimeAdmin(admin.ModelAdmin):
    list_display = ['fiscal_year', 'month', 'uptime_pct', 'incidents', 'downtime_minutes']
    list_filter = ['fiscal_year']


@admin.register(NETCDispute)
class NETCDisputeAdmin(admin.ModelAdmin):
    list_display = ['bank_name', 'fiscal_year', 'month', 'category', 'value']
    list_filter = ['fiscal_year', 'bank_name']


@admin.register(EconomicSurvey)
class EconomicSurveyAdmin(admin.ModelAdmin):
    list_display = ['year', 'total_road_km', 'nh_km', 'sh_km', 'registered_vehicles']
    list_filter = ['year']
