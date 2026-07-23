import json
from pathlib import Path

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from kebun.models import Kebun


class Command(BaseCommand):
    help = "Update geom kebun dari file GeoJSON berdasarkan properties.ID_Kebun (lookup id_kebun lalu id_perbaikan)"

    def add_arguments(self, parser):
        parser.add_argument("geojson_file", type=str, help="Path ke file GeoJSON")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validasi file dan tampilkan perubahan tanpa menyimpan ke database",
        )

    def handle(self, *args, **options):
        geojson_path = Path(options["geojson_file"])
        dry_run = options["dry_run"]

        if not geojson_path.exists():
            raise CommandError(f"File tidak ditemukan: {geojson_path}")

        payload = self._load_geojson(geojson_path)
        features = payload.get("features")
        if not isinstance(features, list):
            raise CommandError("GeoJSON tidak memiliki daftar 'features' yang valid")

        updated_count = 0
        missing_count = 0
        skipped_count = 0
        error_count = 0

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Running in DRY RUN mode - data tidak akan disimpan")
            )

        with transaction.atomic():
            for index, feature in enumerate(features, start=1):
                try:
                    result = self._process_feature(feature=feature, index=index, dry_run=dry_run)
                    if result == "updated":
                        updated_count += 1
                    elif result == "missing":
                        missing_count += 1
                    elif result == "skipped":
                        skipped_count += 1
                except Exception as exc:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f"✗ Feature {index}: {exc}")
                    )

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS(f"Berhasil diproses: {updated_count} feature"))
        self.stdout.write(self.style.WARNING(f"Kebun tidak ditemukan: {missing_count} feature"))
        self.stdout.write(self.style.WARNING(f"Dilewati: {skipped_count} feature"))
        self.stdout.write(self.style.ERROR(f"Error: {error_count} feature"))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN selesai - tidak ada data yang disimpan"))

    def _load_geojson(self, geojson_path):
        try:
            with geojson_path.open("r", encoding="utf-8") as geojson_file:
                return json.load(geojson_file)
        except json.JSONDecodeError as exc:
            raise CommandError(f"File GeoJSON tidak valid: {exc}") from exc
        except OSError as exc:
            raise CommandError(f"Gagal membaca file: {exc}") from exc

    def _get_id_kebun(self, feature):
        properties = feature.get("properties") or {}

        # Beberapa file memakai variasi penamaan key berbeda (contoh: ID_KEBUN).
        candidate_keys = ["ID_Kebun", "ID_KEBUN", "id_kebun", "id_perbaikan", "ID_Perbaikan"]
        id_kebun = None

        for key in candidate_keys:
            value = properties.get(key)
            if value is not None and str(value).strip():
                id_kebun = value
                break

        if id_kebun is None:
            # Case-insensitive fallback to handle other key variations.
            lowered = {str(k).strip().lower(): v for k, v in properties.items()}
            for key in ("id_kebun", "id_perbaikan"):
                value = lowered.get(key)
                if value is not None and str(value).strip():
                    id_kebun = value
                    break

        if id_kebun is None:
            return ""
        return str(id_kebun).strip()

    def _process_feature(self, feature, index, dry_run):
        id_kebun = self._get_id_kebun(feature)
        if not id_kebun:
            self.stdout.write(
                self.style.WARNING(
                    f"⊘ Feature {index}: properties.ID_Kebun not found, skipped"
                )
            )
            return "skipped"

        kebun, lookup_field = self._find_kebun(id_kebun)
        if kebun is None:
            self.stdout.write(
                self.style.WARNING(
                    f"⊘ Feature {index}: Kebun with id_kebun/id_perbaikan {id_kebun} not found"
                )
            )
            return "missing"

        geometry = self._build_geometry(feature, id_kebun)

        if not dry_run:
            kebun.geom = geometry
            kebun.save()

        action_label = "akan diupdate" if dry_run else "diupdate"
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Feature {index}: {id_kebun} ({lookup_field}) berhasil {action_label}"
            )
        )
        return "updated"

    def _find_kebun(self, id_kebun):
        kebun = Kebun.objects.filter(id_kebun=id_kebun).first()
        if kebun:
            return kebun, "lookup: id_kebun"

        kebun = Kebun.objects.filter(id_perbaikan=id_kebun).first()
        if kebun:
            return kebun, "lookup: id_perbaikan"

        return None, None

    def _build_geometry(self, feature, id_kebun):
        geometry_data = feature.get("geometry")
        if not geometry_data:
            raise CommandError(f"Geometry is empty for ID_Kebun {id_kebun}")

        try:
            geometry = GEOSGeometry(json.dumps(geometry_data), srid=4326)
        except Exception as exc:
            raise CommandError(
                f"Invalid GeoJSON geometry for ID_Kebun {id_kebun}: {exc}"
            ) from exc

        if geometry.empty:
            raise CommandError(f"Geometry is empty for ID_Kebun {id_kebun}")

        if geometry.srid is None:
            geometry.srid = 4326
        elif geometry.srid != 4326:
            geometry.transform(4326)

        if geometry.geom_type == "MultiPolygon":
            if len(geometry) != 1:
                raise CommandError(
                    f"MultiPolygon geometry for ID_Kebun {id_kebun} has more than one polygon"
                )
            geometry = geometry[0]

        if geometry.geom_type != "Polygon":
            raise CommandError(
                f"Geometry type {geometry.geom_type} for ID_Kebun {id_kebun} is not supported"
            )

        return geometry