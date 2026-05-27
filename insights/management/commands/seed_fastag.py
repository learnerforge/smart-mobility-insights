from django.core.management.base import BaseCommand
from django.db import transaction

from insights.datasets import fastag
from insights.models import TollPlaza, FASTagTransaction


class Command(BaseCommand):
    help = "Ingest FASTag transaction data from Dataful"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Delete existing data first")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["force"]:
            self.stdout.write("Clearing existing FASTag data...")
            FASTagTransaction.objects.all().delete()
            TollPlaza.objects.all().delete()

        if FASTagTransaction.objects.exists() and not options["force"]:
            self.stdout.write("FASTag data exists. Use --force to re-import.")
            return

        self.stdout.write("Fetching FASTag transaction data...")
        rows = fastag.fetch_transactions_csv()
        if not rows:
            self.stdout.write(self.style.ERROR("No data fetched"))
            return

        parsed = fastag.parse_transactions(rows)
        self.stdout.write(f"Parsed {len(parsed)} transaction records")

        plazas = {}
        created_count = 0
        for rec in parsed:
            lat = rec["latitude"] or 0
            lng = rec["longitude"] or 0
            key = (rec["plaza_name"], rec["state"], round(lat, 4), round(lng, 4))
            if key not in plazas:
                pid = f"{rec['plaza_name']}_{lat}_{lng}".replace(" ", "_").replace(".", "_")
                plaza, was_new = TollPlaza.objects.get_or_create(
                    plaza_id=pid[:100],
                    defaults={
                        "name": rec["plaza_name"],
                        "state": rec["state"],
                        "latitude": lat,
                        "longitude": lng,
                    },
                )
                plazas[key] = plaza
                if was_new:
                    created_count += 1

        batch = []
        for rec in parsed:
            lat = rec["latitude"] or 0
            lng = rec["longitude"] or 0
            plaza = plazas.get((rec["plaza_name"], rec["state"], round(lat, 4), round(lng, 4)))
            if not plaza:
                continue
            batch.append(FASTagTransaction(
                plaza=plaza,
                fiscal_year=rec["fiscal_year"],
                month=rec["month"],
                vehicle_count=rec["vehicle_count"],
                amount_collected=rec["amount_collected"],
            ))

        FASTagTransaction.objects.bulk_create(batch, batch_size=500)
        self.stdout.write(self.style.SUCCESS(
            f"Imported {len(batch)} FASTag transactions across {created_count} plazas ({len(plazas)} unique entries)"
        ))
