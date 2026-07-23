import csv
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from petani.models import Petani
from utils.choices import JenisKelamin, StatusPerkawinan


class Command(BaseCommand):
    help = 'Import data petani dari file CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path ke file CSV')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Jalankan tanpa menyimpan data (testing mode)',
        )

    def parse_date(self, date_str):
        """
        Try parsing the date using multiple formats.
        Return None if parsing fails.
        """
        if not date_str:
            return None
        
        # List of formats to try
        date_formats = [
            '%d-%m-%Y',  # 29-10-2021
            '%d/%m/%Y',  # 29/10/2021
            '%Y-%m-%d',  # 2021-10-29
            '%Y/%m/%d',  # 2021/10/29
            '%d-%m-%y',  # 29-10-21
            '%d/%m/%y',  # 29/10/21
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        
        # Return None if all formats fail
        return None

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - data will not be saved'))

        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as file:
                # Skip BOM if present and read CSV with semicolon delimiter
                csv_reader = csv.DictReader(file, delimiter=';')
                
                success_count = 0
                error_count = 0
                errors = []

                for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (header is row 1)
                    try:
                        with transaction.atomic():
                            # Map gender
                            jk_map = {'L': JenisKelamin.LAKI_LAKI, 'P': JenisKelamin.PEREMPUAN}
                            jenis_kelamin = jk_map.get(row.get('jenis_kelamin', '').strip().upper())
                            
                            if not jenis_kelamin:
                                raise ValueError(f"Jenis kelamin tidak valid: {row.get('jenis_kelamin')}")

                            # Parse date of birth (supports multiple formats)
                            tgl_lahir_str = row.get('tanggal_lahir', '').strip()
                            tanggal_lahir = self.parse_date(tgl_lahir_str)

                            # Parse SPPL issue date (supports multiple formats)
                            tgl_terbit_sppl_str = row.get('tgl_terbit_sppl', '').strip()
                            tgl_terbit_sppl = None
                            if tgl_terbit_sppl_str:
                                # If the format is "Sekadau, 29-10-2021", keep only the date part
                                if ',' in tgl_terbit_sppl_str:
                                    parts = tgl_terbit_sppl_str.split(',', 1)
                                    if len(parts) == 2:
                                        tgl_terbit_sppl_str = parts[1].strip()
                                
                                tgl_terbit_sppl = self.parse_date(tgl_terbit_sppl_str)

                            # Map marital status
                            status_map = {
                                'BELUM KAWIN': StatusPerkawinan.BELUM_KAWIN,
                                'KAWIN': StatusPerkawinan.KAWIN,
                                'CERAI HIDUP': StatusPerkawinan.CERAI_HIDUP,
                                'CERAI MATI': StatusPerkawinan.CERAI_MATI,
                            }
                            status_kawin = row.get('status_kawin', '').strip().upper()
                            status_perkawinan = status_map.get(status_kawin)

                            # Create farmer data
                            petani_data = {
                                'id_petani': row.get('id_petani', '').strip(),
                                'nama': row.get('nama_petani', '').strip(),
                                'nama_kelompok': row.get('nama_kelompok', '').strip(),
                                'jns_kelamin': jenis_kelamin,
                                'no_ktp': row.get('no_ktp', '').strip() or None,
                                'tempat': row.get('tempat_lahir', '').strip(),
                                'tanggal_lahir': tanggal_lahir,
                                'alamat': row.get('alamat_petani', '').strip(),
                                'no_kk': row.get('no_kk', '').strip() or None,
                                'status_perkawinan': status_perkawinan,
                                'no_nib': row.get('no_nib', '').strip() or None,
                                'tgl_terbit_sppl': tgl_terbit_sppl,
                            }

                            # Validate required fields
                            required_fields = ['id_petani', 'nama', 'nama_kelompok', 'jns_kelamin']
                            missing_fields = [field for field in required_fields if not petani_data.get(field)]
                            
                            # Generate a dummy no_ktp if it is missing
                            if not petani_data.get('no_ktp'):
                                petani_data['no_ktp'] = f"NOKTP-{petani_data['id_petani']}"
                                
                            if missing_fields:
                                raise ValueError(f"Field wajib diisi: {', '.join(missing_fields)}")

                            # Check whether id_petani already exists
                            if Petani.objects.filter(id_petani=petani_data['id_petani']).exists():
                                raise ValueError(f"ID Petani {petani_data['id_petani']} sudah ada dalam database")

                            if not dry_run:
                                Petani.objects.create(**petani_data)
                            else:
                                # Roll back in dry-run mode
                                transaction.set_rollback(True)
                            
                            success_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f"✓ Baris {row_num}: {petani_data['nama']} ({petani_data['id_petani']})")
                            )

                    except Exception as e:
                        error_count += 1
                        error_msg = f"✗ Baris {row_num}: {str(e)}"
                        errors.append(error_msg)
                        self.stdout.write(self.style.ERROR(error_msg))

                # Summary
                self.stdout.write('\n' + '='*70)
                self.stdout.write(self.style.SUCCESS(f'Berhasil: {success_count} record'))
                self.stdout.write(self.style.ERROR(f'Gagal: {error_count} record'))
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('\n⚠ DRY RUN MODE - Tidak ada data yang disimpan'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'\n✓ Import selesai! Total {success_count} data petani berhasil disimpan'))

                if errors:
                    self.stdout.write('\n' + self.style.ERROR('Daftar error:'))
                    for error in errors:
                        self.stdout.write(f'  {error}')

        except FileNotFoundError:
            raise CommandError(f'File tidak ditemukan: {csv_file}')
        except Exception as e:
            raise CommandError(f'Error membaca file CSV: {str(e)}')
