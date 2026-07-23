from datetime import datetime, timedelta
from alerts.gee_middleware import GEEGetDataDeforestation
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Generate and export deforestation alerts from Google Earth Engine'

    def handle(self, *args, **options):
        now = datetime.now()
        days_ago_7 = now - timedelta(days=7)
        yesterday = now - timedelta(days=1)
        start_date = days_ago_7.strftime('%Y-%m-%d')
        end_date = yesterday.strftime('%Y-%m-%d')

        gee_deforestation = GEEGetDataDeforestation(start_date, end_date)
        self.stdout.write(self.style.SUCCESS('Export RADD data starting ....'))
        gee_deforestation.radd_export_geojson()

        self.stdout.write(self.style.SUCCESS('Import RADD data to database starting....'))
        gee_deforestation.import_data_radd_to_db()

        self.stdout.write(self.style.SUCCESS('Export GLAD data starting ....'))
        gee_deforestation.glad_export_geojson()

        self.stdout.write(self.style.SUCCESS('Import GLAD data to database starting....'))
        gee_deforestation.import_data_glad_to_db()

        self.stdout.write(self.style.SUCCESS('Export completed successfully'))
