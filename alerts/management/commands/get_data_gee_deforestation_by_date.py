from alerts.gee_middleware import GEEGetDataDeforestation
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Generate and export deforestation alerts from Google Earth Engine'

    def add_arguments(self, parser):
        # add date range
        parser.add_argument('start_date', type=str, help='Date format YYYY-MM-DD')
        parser.add_argument('end_date', type=str, help='Date format YYYY-MM-DD')

    def handle(self, *args, **options):
        gee_deforestation = GEEGetDataDeforestation(options['start_date'], options['end_date'])
        self.stdout.write(self.style.SUCCESS('Export RADD data starting ....'))
        gee_deforestation.radd_export_geojson()

        self.stdout.write(self.style.SUCCESS('Import RADD data to database starting....'))
        gee_deforestation.import_data_radd_to_db()

        self.stdout.write(self.style.SUCCESS('Export GLAD data starting ....'))
        gee_deforestation.glad_export_geojson()

        self.stdout.write(self.style.SUCCESS('Import GLAD data to database starting....'))
        gee_deforestation.import_data_glad_to_db()

        self.stdout.write(self.style.SUCCESS('Export completed successfully'))
