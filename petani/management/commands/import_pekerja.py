import csv
import re
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from petani.models import Pekerja, Petani
from utils.choices import JenisKelamin, StatusPekerja


class Command(BaseCommand):
    help = 'Import data pekerja dari file CSV'

    def __init__(self):
        super().__init__()
        self.success_count = 0
        self.skip_count = 0
        self.error_count = 0
        self.errors = []

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path ke file CSV')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Jalankan tanpa menyimpan data (testing mode)',
        )

    def parse_date(self, date_str):
        if not date_str:
            return None

        normalized = date_str.strip()
        date_formats = [
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d-%m-%y',
            '%d/%m/%y',
            '%d %B %Y',
            '%d %b %Y',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(normalized, fmt).date()
            except ValueError:
                continue

        return None

    def parse_tempat_tgl_lahir(self, raw_value):
        if not raw_value:
            return '', None

        value = raw_value.strip()
        date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]+\s+\d{2,4})$', value)
        if not date_match:
            return value, None

        date_str = date_match.group(1).strip()
        tempat = value[:date_match.start()].rstrip(' ,;')
        return tempat, self.parse_date(date_str)

    def map_jenis_kelamin(self, value):
        return {
            'L': JenisKelamin.LAKI_LAKI,
            'P': JenisKelamin.PEREMPUAN,
        }.get((value or '').strip().upper())

    def map_status_pekerja(self, row):
        status_mapping = [
            ('status_pemilik', StatusPekerja.PEMILIK),
            ('status_family', StatusPekerja.KELUARGA),
            ('status_buruh_tetap', StatusPekerja.BURUH_TETAP),
            ('status_buruh_harian_lepas', StatusPekerja.BURUH_HARIAN_TETAP),
        ]

        for field_name, status_value in status_mapping:
            if (row.get(field_name) or '').strip() == '1':
                return status_value

        return None

    def log_skip(self, row_num, message):
        self.skip_count += 1
        self.stdout.write(self.style.WARNING(f"⊘ Baris {row_num}: {message}"))

    def log_error(self, row_num, error):
        self.error_count += 1
        error_msg = f"✗ Baris {row_num}: {str(error)}"
        self.errors.append(error_msg)
        self.stdout.write(self.style.ERROR(error_msg))

    def get_petani(self, row_num, id_petani):
        if not id_petani:
            self.log_skip(row_num, 'id_petani kosong, dilewati')
            return None

        try:
            return Petani.objects.get(id_petani=id_petani)
        except Petani.DoesNotExist:
            self.log_skip(row_num, f"Petani dengan ID '{id_petani}' tidak ditemukan, dilewati")
            return None

    def build_pekerja_data(self, row):
        jenis_kelamin = self.map_jenis_kelamin(row.get('jns_kelamin'))

        tempat_lahir, tanggal_lahir = self.parse_tempat_tgl_lahir(row.get('tempat_tgl_lahir') or '')

        return {
            'jns_kelamin': jenis_kelamin,
            'kelompok_tani': (row.get('nama_kelompok') or '').strip() or None,
            'alamat': (row.get('alamat') or '').strip() or None,
            'no_ktp': (row.get('no_ktp') or '').strip() or None,
            'tempat_lahir': tempat_lahir or None,
            'tanggal_lahir': tanggal_lahir,
            'no_kk': (row.get('no_kk') or '').strip() or None,
            'status_pekerja': self.map_status_pekerja(row),
        }

    def upsert_pekerja(self, petani, nama_pekerja, pekerja_data, dry_run):
        if not dry_run:
            _, created = Pekerja.objects.update_or_create(
                petani=petani,
                nama=nama_pekerja,
                defaults=pekerja_data,
            )
            return 'dibuat' if created else 'diupdate'

        exists = Pekerja.objects.filter(petani=petani, nama=nama_pekerja).exists()
        return 'akan diupdate' if exists else 'akan dibuat'

    def process_row(self, row_num, row, dry_run):
        id_petani = (row.get('id_petani') or '').strip()
        nama_pekerja = (row.get('nama_pekerja') or '').strip()

        if not id_petani or not nama_pekerja:
            self.log_skip(row_num, 'id_petani atau nama_pekerja kosong, dilewati')
            return

        petani = self.get_petani(row_num, id_petani)
        if not petani:
            return

        pekerja_data = self.build_pekerja_data(row)
        action = self.upsert_pekerja(petani, nama_pekerja, pekerja_data, dry_run)

        self.success_count += 1
        status_label = pekerja_data['status_pekerja'] or '-'
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Baris {row_num}: {nama_pekerja} ({id_petani}) {action} | status: {status_label}"
            )
        )

    def print_summary(self, dry_run):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS(f'Berhasil: {self.success_count} record'))
        self.stdout.write(self.style.WARNING(f'Dilewati: {self.skip_count} record'))
        self.stdout.write(self.style.ERROR(f'Gagal: {self.error_count} record'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠ DRY RUN MODE - Tidak ada data yang disimpan'))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Import selesai! Total {self.success_count} data pekerja berhasil diproses'
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
        except Exception as e:
            raise CommandError(f'Error membaca file CSV: {str(e)}')