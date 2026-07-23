import django_rq
from django.core.management.base import BaseCommand

from kebun.models import Kebun, KebunDeforestationAnalysis
from utils.choices import WHISPStatus
from utils.whisp import WHISPService


class Command(BaseCommand):
    help = 'Enqueue WHISP analysis jobs for kebun records that have geometry'

    def add_arguments(self, parser):
        parser.add_argument(
            '--kebun-id',
            type=str,
            default=None,
            dest='kebun_id',
            help='Jalankan analisis untuk satu kebun saja berdasarkan id_kebun.',
        )
        parser.add_argument(
            '--status',
            type=str,
            default=None,
            help=(
                'Filter berdasarkan whisp_status yang ingin di-rerun '
                '(comma-separated, misal: pending,error). '
                'Jika tidak diisi, hanya kebun yang belum punya KebunDeforestationAnalysis yang diproses.'
            ),
        )
        parser.add_argument(
            '--all',
            action='store_true',
            dest='run_all',
            help='Enqueue semua kebun dengan geom, termasuk yang sudah completed.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Tampilkan daftar kebun yang akan diproses tanpa benar-benar enqueue job.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        run_all = options['run_all']
        status_filter = options['status']
        kebun_id_filter = options['kebun_id']

        kebun_qs = Kebun.objects.filter(geom__isnull=False)

        if kebun_id_filter:
            try:
                kebun = kebun_qs.get(id_kebun=kebun_id_filter)
            except Kebun.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f"Kebun dengan id_kebun='{kebun_id_filter}' tidak ditemukan atau tidak memiliki geom."
                ))
                return
            target_ids = [kebun.id]
            label = f"kebun id_kebun={kebun_id_filter}"
        elif run_all:
            target_ids = list(kebun_qs.values_list('id', flat=True))
            label = "semua kebun dengan geom"
        elif status_filter:
            statuses = [s.strip() for s in status_filter.split(',')]
            analysis_ids = KebunDeforestationAnalysis.objects.filter(
                whisp_status__in=statuses
            ).values_list('kebun_id', flat=True)
            target_ids = list(kebun_qs.filter(id__in=analysis_ids).values_list('id', flat=True))
            label = f"kebun dengan status: {', '.join(statuses)}"
        else:
            # Default: kebun records without any KebunDeforestationAnalysis yet
            existing_ids = KebunDeforestationAnalysis.objects.values_list('kebun_id', flat=True)
            target_ids = list(kebun_qs.exclude(id__in=existing_ids).values_list('id', flat=True))
            label = "kebun yang belum punya analisis"

        total = len(target_ids)

        if total == 0:
            self.stdout.write(self.style.WARNING(f"Tidak ada kebun yang cocok ({label})."))
            return

        self.stdout.write(f"Ditemukan {total} kebun ({label}).")

        if dry_run:
            self.stdout.write(self.style.WARNING(f"[DRY-RUN] {total} job akan dienqueue. Tidak ada yang diproses."))
            for kebun_id in target_ids:
                self.stdout.write(f"  - kebun id={kebun_id}")
            return

        whisp_service = WHISPService()
        queue = django_rq.get_queue('default')
        enqueued = 0

        for kebun_id in target_ids:
            queue.enqueue(whisp_service.process_whisp_analysis, kebun_id)
            enqueued += 1
            self.stdout.write(f"  ✓ Enqueued kebun id={kebun_id} ({enqueued}/{total})")

        self.stdout.write(self.style.SUCCESS(
            f"\nSelesai. {enqueued} job berhasil dienqueue ke RQ queue 'default'."
        ))
