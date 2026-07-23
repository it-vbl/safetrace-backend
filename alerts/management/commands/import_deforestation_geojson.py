import json
from datetime import date
from pathlib import Path

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from alerts.models import DeforeStation


class Command(BaseCommand):
    help = "Import data deforestasi dari file GeoJSON ke model DeforeStation"

    def add_arguments(self, parser):
        parser.add_argument("geojson_file", type=str, help="Path ke file GeoJSON")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validasi dan simulasi import tanpa menyimpan data",
        )

    @staticmethod
    def _parse_date(value):
        if not value:
            raise ValueError("properties.date kosong")
        return date.fromisoformat(str(value))

    @staticmethod
    def _parse_source_type(value):
        if not value:
            raise ValueError("properties.alert_type kosong")
        return str(value).strip().lower()

    @staticmethod
    def _build_geometry(geometry_data):
        if not geometry_data:
            raise ValueError("geometry kosong")

        try:
            geometry = GEOSGeometry(json.dumps(geometry_data), srid=4326)
        except Exception as exc:
            raise ValueError(f"geometry tidak valid: {exc}") from exc

        if geometry.empty:
            raise ValueError("geometry kosong")

        if geometry.srid is None:
            geometry.srid = 4326
        elif geometry.srid != 4326:
            geometry.transform(4326)

        if geometry.geom_type == "Polygon":
            geometry = MultiPolygon(geometry)
        elif geometry.geom_type != "MultiPolygon":
            raise ValueError(f"tipe geometry tidak didukung: {geometry.geom_type}")

        return geometry

    def handle(self, *args, **options):
        geojson_path = Path(options["geojson_file"])
        dry_run = options["dry_run"]

        if not geojson_path.exists():
            raise CommandError(f"File tidak ditemukan: {geojson_path}")

        try:
            with geojson_path.open("r", encoding="utf-8") as geojson_file:
                payload = json.load(geojson_file)
        except json.JSONDecodeError as exc:
            raise CommandError(f"File GeoJSON tidak valid: {exc}") from exc
        except OSError as exc:
            raise CommandError(f"Gagal membaca file: {exc}") from exc

        features = payload.get("features")
        if not isinstance(features, list):
            raise CommandError("GeoJSON tidak memiliki daftar 'features' yang valid")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Running in DRY RUN mode - data tidak akan disimpan")
            )

        success_count = 0
        error_count = 0

        with transaction.atomic():
            for index, feature in enumerate(features, start=1):
                try:
                    if not isinstance(feature, dict):
                        raise ValueError("feature bukan object")

                    properties = feature.get("properties") or {}
                    geometry_data = feature.get("geometry")

                    date_value = self._parse_date(properties.get("date"))
                    label_raw = properties.get("label")
                    if label_raw in (None, ""):
                        raise ValueError("properties.label kosong")

                    source_type = self._parse_source_type(properties.get("alert_type"))
                    area_ha = float(properties.get("hectares") or 0.0)
                    geom = self._build_geometry(geometry_data)

                    label = f"{label_raw}-{date_value.isoformat()}"

                    if not dry_run:
                        DeforeStation.objects.create(
                            label=label,
                            date=date_value,
                            source_type=source_type,
                            geom=geom,
                            area_ha=area_ha,
                        )

                    success_count += 1
                    action = "akan diimport" if dry_run else "diimport"
                    self.stdout.write(self.style.SUCCESS(f"✓ Feature {index}: {label} {action}"))

                except Exception as exc:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f"✗ Feature {index}: {exc}"))

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS(f"Berhasil: {success_count} feature"))
        self.stdout.write(self.style.ERROR(f"Gagal: {error_count} feature"))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN selesai - tidak ada data yang disimpan"))