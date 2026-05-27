import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from insights.models import EconomicSurvey

logger = logging.getLogger(__name__)

HISTORICAL_DATA = [
    {"year": 1961, "total_road_km": 524500, "nh_km": 23800, "registered_vehicles": 665000},
    {"year": 1971, "total_road_km": 915000, "nh_km": 23800, "registered_vehicles": 1865000},
    {"year": 1981, "total_road_km": 1587500, "nh_km": 31700, "registered_vehicles": 5391000},
    {"year": 1991, "total_road_km": 2337400, "nh_km": 33700, "registered_vehicles": 21374000},
    {"year": 2001, "total_road_km": 3373500, "surfaced_road_km": 1101700, "nh_km": 57700, "registered_vehicles": 54991000},
    {"year": 2012, "total_road_km": 4865400, "surfaced_road_km": 2698600, "nh_km": 76800, "registered_vehicles": 159491000},
    {"year": 2014, "total_road_km": 5402486, "surfaced_road_km": 3220500, "nh_km": 91287, "sh_km": 170818, "registered_vehicles": 190704000},
    {"year": 2015, "total_road_km": 5472144, "surfaced_road_km": 3305900, "nh_km": 97991, "sh_km": 167109, "registered_vehicles": 210230000},
    {"year": 2019, "total_road_km": 6331757, "surfaced_road_km": 4095725, "nh_km": 132995, "registered_vehicles": 295772000},
    {"year": 2020, "total_road_km": 6360004, "surfaced_road_km": 4129448, "nh_km": 132995, "registered_vehicles": 326300000},
    {"year": 2024, "total_road_km": 6340000, "surfaced_road_km": 4500000, "nh_km": 146195, "sh_km": 178749},
]


class Command(BaseCommand):
    help = "Seed Economic Survey road transport data"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Replace existing data")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["force"]:
            EconomicSurvey.objects.all().delete()

        count = 0
        for rec in HISTORICAL_DATA:
            _, created = EconomicSurvey.objects.update_or_create(
                year=rec["year"],
                defaults=rec,
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {count} new + {len(HISTORICAL_DATA) - count} existing Economic Survey records"))
