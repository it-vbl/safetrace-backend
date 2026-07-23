import time
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from alerts.models import DeforeStation
from alerts.utils import (
    _load_active_layer_static_geometries,
    get_adm_desa_by_area,
    get_intersected_layer_static,
)


class Command(BaseCommand):
    help = "Reanalyze stored deforestation data for LayerStatic intersections and adm desa"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start-date",
            type=str,
            help="Date format YYYY-MM-DD. Optional.",
        )
        parser.add_argument(
            "--end-date",
            type=str,
            help="Date format YYYY-MM-DD. Optional.",
        )

    def handle(self, *args, **options):
        start_date_value = options.get("start_date")
        end_date_value = options.get("end_date")

        start_date = None
        end_date = None

        try:
            if start_date_value:
                start_date = date.fromisoformat(start_date_value)
            if end_date_value:
                end_date = date.fromisoformat(end_date_value)
        except ValueError as exc:
            raise CommandError("Invalid date format. Use YYYY-MM-DD format.") from exc

        if start_date and end_date and start_date > end_date:
            raise CommandError("start_date must be less than or equal to end_date.")

        start_time = time.time()
        parsed_layers = _load_active_layer_static_geometries()

        queryset = DeforeStation.objects.all()

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        queryset = queryset.order_by("id")
        total = queryset.count()

        self.stdout.write(self.style.SUCCESS(f"Found {total} deforestation records to reanalyze."))

        success_count = 0
        error_count = 0

        for deforestation in queryset:
            try:
                geom = deforestation.geom
                impacted_layers = get_intersected_layer_static(geom, parsed_layers)
                adm_desa = get_adm_desa_by_area(geom)

                raw_data = deforestation.raw_data or {}
                raw_data.update({
                    "layer_static_intersections": impacted_layers,
                    "layer_static_intersection_count": len(impacted_layers),
                })

                deforestation.raw_data = raw_data
                deforestation.save(update_fields=["raw_data", "administrative_area", "updated_at"])
                deforestation.save_adm_desa_data(adm_desa)

                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Deforestation {deforestation.id} reanalyzed"
                    )
                )
            except Exception as exc:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Deforestation {deforestation.id} failed: {exc}"
                    )
                )

        elapsed = time.time() - start_time
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS(f"Berhasil: {success_count} record"))
        self.stdout.write(self.style.ERROR(f"Gagal: {error_count} record"))
        self.stdout.write(self.style.SUCCESS(f"Selesai dalam {elapsed:.2f} detik"))