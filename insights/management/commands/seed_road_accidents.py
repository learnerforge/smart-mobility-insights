from django.core.management.base import BaseCommand
from django.db import transaction

from insights.datasets import road_accidents
from insights.models import RoadAccident, RoadAccidentByCollision, RoadAccidentByRoadUser


class Command(BaseCommand):
    help = "Ingest Road Accident statistics from MoRTH/Dataful/OpenCity"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Delete existing data first")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["force"]:
            self.stdout.write("Clearing existing accident data...")
            RoadAccident.objects.all().delete()
            RoadAccidentByCollision.objects.all().delete()
            RoadAccidentByRoadUser.objects.all().delete()

        if RoadAccident.objects.exists() and not options["force"]:
            self.stdout.write("Accident data exists. Use --force to re-import.")
            return

        self.stdout.write("Fetching road accident violations data...")
        rows = road_accidents.fetch_violations_csv()
        if rows:
            parsed = road_accidents.parse_violations(rows)
            batch = [RoadAccident(**rec) for rec in parsed]
            RoadAccident.objects.bulk_create(batch, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"Imported {len(batch)} violation records"))
        else:
            self.stdout.write(self.style.WARNING("No violation data fetched"))

        self.stdout.write("Fetching collision type data...")
        collision_rows = road_accidents.fetch_collision_csv()
        if collision_rows:
            parsed = road_accidents.parse_collisions(collision_rows)
            batch = [RoadAccidentByCollision(**rec) for rec in parsed]
            RoadAccidentByCollision.objects.bulk_create(batch, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"Imported {len(batch)} collision records"))
        else:
            self.stdout.write(self.style.WARNING("No collision data fetched"))

        self.stdout.write("Fetching road user type data...")
        user_rows = road_accidents.fetch_road_users_csv()
        if user_rows:
            parsed = road_accidents.parse_road_users(user_rows)
            batch = [RoadAccidentByRoadUser(**rec) for rec in parsed]
            RoadAccidentByRoadUser.objects.bulk_create(batch, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"Imported {len(batch)} road user records"))
        else:
            self.stdout.write(self.style.WARNING("No road user data fetched"))
