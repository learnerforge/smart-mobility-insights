from django.core.management.base import BaseCommand
from django.db import transaction

from insights.datasets import road_statistics
from insights.models import RoadStatistic


class Command(BaseCommand):
    help = "Ingest Basic Road Statistics from MoRTH/Dataful"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Delete existing data first")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["force"]:
            self.stdout.write("Clearing existing road statistics...")
            RoadStatistic.objects.all().delete()

        if RoadStatistic.objects.exists() and not options["force"]:
            self.stdout.write("Road statistics exist. Use --force to re-import.")
            return

        self.stdout.write("Fetching road length data...")
        rows = road_statistics.fetch_road_length_csv()
        if not rows:
            self.stdout.write(self.style.ERROR("No data fetched"))
            return

        parsed = road_statistics.parse_road_lengths(rows)
        batch = [RoadStatistic(**rec) for rec in parsed]
        RoadStatistic.objects.bulk_create(batch, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f"Imported {len(batch)} road statistic records"))
