from django.urls import path
from . import views

urlpatterns = [
    path("", views.map_view, name="map"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("api/geocode/", views.api_geocode, name="api_geocode"),
    path("api/reverse-geocode/", views.api_reverse_geocode, name="api_reverse_geocode"),
    path("api/route/", views.api_route, name="api_route"),
    path("api/trips/", views.api_trips, name="api_trips"),
    path("api/admin/stats/", views.api_admin_stats, name="api_admin_stats"),
    path("api/road-conditions/", views.api_road_conditions, name="api_road_conditions"),
    path("api/road-conditions/report/", views.api_report_road_condition, name="api_report_road_condition"),
    path("api/road-conditions/<int:condition_id>/resolve/", views.api_resolve_road_condition, name="api_resolve_road_condition"),
    path("api/road-conditions/stats/", views.api_road_condition_stats, name="api_road_condition_stats"),
    path("api/fastag/stats/", views.api_fastag_stats, name="api_fastag_stats"),
    path("api/toll-plazas/", views.api_toll_plazas, name="api_toll_plazas"),
    path("api/national-highways/", views.api_national_highways, name="api_national_highways"),
    path("api/road-accidents/stats/", views.api_road_accident_stats, name="api_road_accident_stats"),
    path("api/road-statistics/", views.api_road_statistics, name="api_road_statistics"),
    path("api/netc/stats/", views.api_netc_stats, name="api_netc_stats"),
    path("api/economic-survey/", views.api_economic_survey, name="api_economic_survey"),
    path("api/road-collisions/stats/", views.api_road_collision_stats, name="api_road_collision_stats"),
    path("api/road-users/stats/", views.api_road_user_stats, name="api_road_user_stats"),
    path("api/netc/disputes/", views.api_netc_disputes, name="api_netc_disputes"),
    path("health/", views.health_check, name="health_check"),
]
