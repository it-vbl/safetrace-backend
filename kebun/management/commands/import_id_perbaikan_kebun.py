import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from kebun.models import Kebun


class Command(BaseCommand):
    help = 'Import dan update id_perbaikan kebun dari file CSV berdasarkan id_kebun'

    def __init__(self):
        super().__init__()
        self.updated_count = 0
        self.skip_count = 0
        self.no_change_count = 0
        self.error_count = 0
        self.errors = []

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path ke file CSV')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Jalankan tanpa menyimpan data (testing mode)',
        )

    def validate_headers(self, csv_reader):
        required_headers = {'id_kebun', 'id_perbaikan'}
        missing_headers = required_headers - set(csv_reader.fieldnames or [])
        if missing_headers:
            raise CommandError(
                f"Kolom wajib tidak ditemukan di CSV: {', '.join(sorted(missing_headers))}"
            )

    def log_skip(self, row_num, message):
        self.skip_count += 1
        self.stdout.write(self.style.WARNING(f"⊘ Baris {row_num}: {message}"))

    def log_error(self, row_num, error):
        self.error_count += 1
        error_msg = f"✗ Baris {row_num}: {str(error)}"
        self.errors.append(error_msg)
        self.stdout.write(self.style.ERROR(error_msg))

    def process_row(self, row_num, row, dry_run):
        id_kebun = (row.get('id_kebun') or '').strip()
        id_perbaikan = (row.get('id_perbaikan') or '').strip() or None

        if not id_kebun:
            self.log_skip(row_num, 'id_kebun kosong, dilewati')
            return

        try:
            kebun = Kebun.objects.get(id_kebun=id_kebun)
        except Kebun.DoesNotExist:
            self.log_skip(row_num, f"Kebun dengan ID '{id_kebun}' tidak ditemukan, dilewati")
            return

        if kebun.id_perbaikan == id_perbaikan:
            self.no_change_count += 1
            self.stdout.write(
                self.style.WARNING(
                    f"⊘ Baris {row_num}: {kebun.id_kebun} ({kebun.petani.nama}) tidak berubah"
                )
            )
            return

        before = kebun.id_perbaikan or '-'
        after = id_perbaikan or '-'

        if not dry_run:
            kebun.id_perbaikan = id_perbaikan
            kebun.save(update_fields=['id_perbaikan', 'updated_at'])

        self.updated_count += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Baris {row_num}: {kebun.id_kebun} | {before} -> {after}"
            )
        )

    def print_summary(self, dry_run):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS(f'Berhasil update: {self.updated_count} record'))
        self.stdout.write(self.style.WARNING(f'Tidak ditemukan/invalid: {self.skip_count} record'))
        self.stdout.write(self.style.WARNING(f'Tidak berubah: {self.no_change_count} record'))
        self.stdout.write(self.style.ERROR(f'Gagal: {self.error_count} record'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠ DRY RUN MODE - Tidak ada data yang disimpan'))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Import selesai! Total {self.updated_count} data id_perbaikan kebun berhasil diupdate'
                )
            )

        if self.errors:
            self.stdout.write('\n' + self.style.ERROR('Daftar error:'))
            for error in self.errors[:20]:
                self.stdout.write(f'  {error}')
            if len(self.errors) > 20:
                self.stdout.write(f'  ... dan {len(self.errors) - 20} error lainnya')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - data will not be saved'))

        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file, delimiter=';')
                self.validate_headers(csv_reader)

                with transaction.atomic():
                    for row_num, row in enumerate(csv_reader, start=2):
                        try:
                            self.process_row(row_num, row, dry_run)
                        except Exception as e:
                            self.log_error(row_num, e)

                    if dry_run:
                        transaction.set_rollback(True)

                self.print_summary(dry_run)

        except FileNotFoundError:
            raise CommandError(f'File tidak ditemukan: {csv_file}')
        except CommandError:
            raise
        except Exception as e:
            raise CommandError(f'Error membaca file CSV: {str(e)}')