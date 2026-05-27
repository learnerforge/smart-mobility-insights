from django.core.management.base import BaseCommand
from django.db import transaction

from insights.datasets import netc_performance
from insights.models import NETCProcessingRate, NETCUptime, NETCDispute


class Command(BaseCommand):
    help = "Ingest NETC FASTag performance data from Dataful"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Delete existing data first")
        parser.add_argument("--sections", nargs="+", default=["rates", "uptime", "disputes"],
                            help="Sections to import: rates, uptime, disputes")

    @transaction.atomic
    def handle(self, *args, **options):
        sections = options["sections"]

        if options["force"]:
            if "rates" in sections:
                NETCProcessingRate.objects.all().delete()
            if "uptime" in sections:
                NETCUptime.objects.all().delete()
            if "disputes" in sections:
                NETCDispute.objects.all().delete()

        if "rates" in sections and (not NETCProcessingRate.objects.exists() or options["force"]):
            self.stdout.write("Loading processing rates...")
            parsed = netc_performance.parse_processing_rates(netc_performance.SAMPLE_PROCESSING_RATES)
            NETCProcessingRate.objects.bulk_create(
                [NETCProcessingRate(**r) for r in parsed], batch_size=500
            )
            self.stdout.write(self.style.SUCCESS(f"Imported {len(parsed)} processing rate records"))

        if "uptime" in sections and (not NETCUptime.objects.exists() or options["force"]):
            self.stdout.write("Loading uptime data...")
            parsed = netc_performance.parse_uptime(netc_performance.SAMPLE_UPTIME)
            NETCUptime.objects.bulk_create(
                [NETCUptime(**r) for r in parsed], batch_size=500
            )
            self.stdout.write(self.style.SUCCESS(f"Imported {len(parsed)} uptime records"))

        if "disputes" in sections and (not NETCDispute.objects.exists() or options["force"]):
            self.stdout.write("Loading dispute data...")
            parsed = netc_performance.parse_disputes(netc_performance.SAMPLE_DISPUTES)
            NETCDispute.objects.bulk_create(
                [NETCDispute(**r) for r in parsed], batch_size=500
            )
            self.stdout.write(self.style.SUCCESS(f"Imported {len(parsed)} dispute records"))
