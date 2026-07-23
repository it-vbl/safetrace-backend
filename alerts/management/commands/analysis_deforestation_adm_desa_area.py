import time
from datetime import datetime
from django.core.management.base import BaseCommand
from alerts.models import DeforeStation
from alerts.utils import get_adm_desa_by_area


class Command(BaseCommand):
    help = 'to insert Soil Type to deforestation'

    def add_arguments(self, parser):
        parser.add_argument('start_date', type=str, help='Date format YYYY-MM-DD')
        parser.add_argument('end_date', type=str, help='Date format YYYY-MM-DD')

    def handle(self, *args, **options):
        # Parsing string into format datetime
        try:
            start_date = datetime.strptime(options['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(options['end_date'], '%Y-%m-%d')
        except ValueError:
            self.stdout.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD format.'))
            return

        start_time = time.time()
        defs = DeforeStation.objects.filter(date__gte=start_date, date__lte=end_date)
        for d in defs:
            adm_desa = get_adm_desa_by_area(d.geom)
            d.save_adm_desa_data(adm_desa)
            self.stdout.write(self.style.SUCCESS(f'Success insert adm desa into deforestation id: {d.id}'))
        self.stdout.write(self.style.SUCCESS("--- %s seconds ---" % (time.time() - start_time)))
