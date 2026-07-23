import json
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from alerts.models import AdmDesaArea


class Command(BaseCommand):
    help = 'Import Administrasi Desa Area into database'

    @staticmethod
    def _strip_z_from_coords(coords):
        if isinstance(coords, (list, tuple)):
            if coords and isinstance(coords[0], (int, float)):
                return coords[:2]
            return [Command._strip_z_from_coords(c) for c in coords]
        return coords

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Full path')

    def handle(self, *args, **options):
        # Read file
        with open(options['file_path'], 'r') as f:
            geojson_data = json.load(f)
        self.stdout.write(self.style.SUCCESS(f'Read File {options["file_path"]}'))

        for feature in geojson_data['features']:
            geometry = feature['geometry']
            properties = feature['properties']

            # Convert geometry to MultiPolygon
            if geometry and 'coordinates' in geometry:
                geometry = dict(geometry)
                geometry['coordinates'] = self._strip_z_from_coords(geometry['coordinates'])
            geom = GEOSGeometry(json.dumps(geometry))
            if geom.geom_type == 'Polygon':
                geom = MultiPolygon(geom)

            # Map administrative fields from properties
            provinsi = properties.get('ProvID') or properties.get('provinsi') or 'Unknown'
            kabupaten = properties.get('DistrictID') or properties.get('kabupaten') or 'Unknown'
            kecamatan = properties.get('SubdistID') or properties.get('kecamatan') or 'Unknown'
            desa = properties.get('VillageID') or properties.get('desa') or 'Unknown'

            # Save to model
            adm_desa = AdmDesaArea.objects.create(
                provinsi=provinsi,
                kabupaten=kabupaten,
                kecamatan=kecamatan,
                desa=desa,
                properties=properties,
                geom=geom
            )

            self.stdout.write(self.style.SUCCESS(
                f'Successfully imported {adm_desa.desa}-{adm_desa.kecamatan}-{adm_desa.kabupaten}-{adm_desa.provinsi}'
            ))
