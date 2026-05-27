from django.core.management.base import BaseCommand
from django.db import transaction

from insights.datasets import nh_geospatial
from insights.models import NationalHighway


class Command(BaseCommand):
    help = "Ingest National Highway geospatial data"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Delete existing data first")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["force"]:
            self.stdout.write("Clearing existing NH data...")
            NationalHighway.objects.all().delete()

        if NationalHighway.objects.exists() and not options["force"]:
            self.stdout.write("NH data exists. Use --force to re-import.")
            return

        self.stdout.write("Fetching National Highway GeoJSON (~50MB)...")
        geojson = nh_geospatial.fetch_national_highways_geojson()
        if not geojson:
            self.stdout.write(self.style.ERROR("No data fetched"))
            return

        parsed = nh_geospatial.parse_highways(geojson)
        self.stdout.write(f"Parsed {len(parsed)} highway features")

        batch = []
        for rec in parsed:
            batch.append(NationalHighway(
                nh_number=rec["nh_number"],
                name=rec["name"],
                length_km=rec["length_km"],
                geometry=rec["geometry"],
            ))

        NationalHighway.objects.bulk_create(batch, batch_size=200)
        self.stdout.write(self.style.SUCCESS(f"Imported {len(batch)} national highway features"))
