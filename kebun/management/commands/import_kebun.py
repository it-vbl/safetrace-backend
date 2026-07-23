import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point
from django.db import transaction
from kebun.models import Kebun
from petani.models import Petani
from utils.choices import JenisLegalitas


class Command(BaseCommand):
    help = 'Import data kebun dari file CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path ke file CSV')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Jalankan tanpa menyimpan data (testing mode)',
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - data will not be saved'))

        # Dictionary for mapping Indonesian month names to numbers
        bulan_map = {
            'JANUARI': 1, 'FEBRUARI': 2, 'MARET': 3, 'APRIL': 4,
            'MEI': 5, 'JUNI': 6, 'JULI': 7, 'AGUSTUS': 8,
            'SEPTEMBER': 9, 'OKTOBER': 10, 'NOVEMBER': 11, 'DESEMBER': 12
        }

        # Dictionary for mapping legality types
        legalitas_map = {
            'SHM': JenisLegalitas.SHM,
            'SKT': JenisLegalitas.SKT,
            'SP': JenisLegalitas.SP,
            'SJB': JenisLegalitas.SJB,
            'SPT': JenisLegalitas.SPT,
        }

        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file, delimiter=';')
                
                success_count = 0
                error_count = 0
                errors = []

                with transaction.atomic():
                    for row_num, row in enumerate(csv_reader, start=2):
                        try:
                            # Skip if id_kebun is missing
                            id_kebun = row.get('id_kebun', '').strip()
                            if not id_kebun:
                                self.stdout.write(
                                    self.style.WARNING(f"⊘ Baris {row_num}: Tidak ada id_kebun, dilewati")
                                )
                                continue

                            # Find the farmer by nama_petani and kelompok_tani
                            nama_petani = row.get('nama_petani', '').strip()
                            kelompok_tani = row.get('kelompok_tani', '').strip()

                            if not nama_petani or not kelompok_tani:
                                raise ValueError(
                                    f"Nama petani atau kelompok tani kosong"
                                )

                            # Find the farmer
                            try:
                                petani = Petani.objects.get(
                                    nama__iexact=nama_petani,
                                    nama_kelompok__iexact=kelompok_tani
                                )
                            except Petani.DoesNotExist:
                                raise ValueError(
                                    f"Petani '{nama_petani}' dari kelompok '{kelompok_tani}' tidak ditemukan di database"
                                )
                            except Petani.MultipleObjectsReturned:
                                raise ValueError(
                                    f"Ditemukan lebih dari 1 petani dengan nama '{nama_petani}' di kelompok '{kelompok_tani}'"
                                )

                            # Parse kebun area
                            luas_str = row.get('luas_kebun', '').strip().replace(',', '.')
                            try:
                                luas = Decimal(luas_str) if luas_str else Decimal('0.0')
                            except (InvalidOperation, ValueError):
                                raise ValueError(f"Luas kebun tidak valid: {luas_str}")

                            # Parse planting time (month + year)
                            bulan_str = row.get('waktu_tanam_bulan', '').strip().upper()
                            tahun_str = row.get('waktu_tanam_tahun', '').strip()
                            waktu_tanam = None
                            
                            if bulan_str and tahun_str:
                                bulan = bulan_map.get(bulan_str)
                                if not bulan:
                                    raise ValueError(f"Bulan tidak valid: {bulan_str}")
                                
                                try:
                                    tahun = int(tahun_str)
                                    # Set the date to the first day of that month
                                    waktu_tanam = datetime(tahun, bulan, 1).date()
                                except ValueError:
                                    raise ValueError(f"Tahun tidak valid: {tahun_str}")

                            # Parse tree count
                            jumlah_pokok_str = row.get('jumlah_pokok', '').strip()
                            try:
                                jumlah_pokok = int(jumlah_pokok_str) if jumlah_pokok_str else 0
                            except ValueError:
                                raise ValueError(f"Jumlah pokok tidak valid: {jumlah_pokok_str}")

                            # Parse RSPO
                            rspo_str = row.get('rspo', '').strip()
                            is_rspo = rspo_str == '1'

                            # Parse ISPO
                            ispo_str = row.get('ispo', '').strip()
                            is_ispo = ispo_str == '1'

                            # Parse legality type
                            jenis_legalitas_str = row.get('jenis_legalitas', '').strip().upper()
                            jenis_legalitas = legalitas_map.get(jenis_legalitas_str) if jenis_legalitas_str else None

                            # Parse coordinates (long, lat)
                            long_str = row.get('long', '').strip().replace(',', '.')
                            lat_str = row.get('lat', '').strip().replace(',', '.')
                            titik_koordinat = None
                            
                            if long_str and lat_str:
                                try:
                                    longitude = float(long_str)
                                    latitude = float(lat_str)
                                    titik_koordinat = Point(longitude, latitude)
                                except (ValueError, TypeError):
                                    raise ValueError(f"Koordinat tidak valid: long={long_str}, lat={lat_str}")

                            # Create kebun data
                            kebun_data = {
                                'id_kebun': id_kebun,
                                'petani': petani,
                                'lokasi_kebun': row.get('lokasi_kebun', '').strip(),
                                'luas': luas,
                                'waktu_tanam': waktu_tanam,
                                'jumlah_pokok': jumlah_pokok,
                                'is_rspo': is_rspo,
                                'is_ispo': is_ispo,
                                'jenis_legalitas': jenis_legalitas,
                                'nomor_legalitas': row.get('no_legalitas', '').strip() or None,
                                'pemilik_legalitas': row.get('nama_pemilik_legalitas', '').strip() or None,
                                'nomor_stdb': row.get('no_stdb', '').strip() or None,
                                'titik_koordinat': titik_koordinat,
                            }

                            # Validate required fields
                            if not kebun_data['lokasi_kebun']:
                                raise ValueError("Lokasi kebun wajib diisi")

                            # Check whether id_kebun already exists
                            if Kebun.objects.filter(id_kebun=id_kebun).exists():
                                raise ValueError(f"ID Kebun {id_kebun} sudah ada dalam database")

                            if not dry_run:
                                Kebun.objects.create(**kebun_data)
                            
                            success_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✓ Baris {row_num}: {id_kebun} - {petani.nama} ({kelompok_tani})"
                                )
                            )

                        except Exception as e:
                            error_count += 1
                            error_msg = f"✗ Baris {row_num}: {str(e)}"
                            errors.append(error_msg)
                            self.stdout.write(self.style.ERROR(error_msg))

                    if dry_run:
                        # Roll back the transaction in dry-run mode
                        transaction.set_rollback(True)

                # Summary
                self.stdout.write('\n' + '='*70)
                self.stdout.write(self.style.SUCCESS(f'Berhasil: {success_count} record'))
                self.stdout.write(self.style.ERROR(f'Gagal: {error_count} record'))
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('\n⚠ DRY RUN MODE - Tidak ada data yang disimpan'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'\n✓ Import selesai! Total {success_count} data kebun berhasil disimpan'))

                if errors:
                    self.stdout.write('\n' + self.style.ERROR('Daftar error:'))
                    for error in errors[:20]:  # Show only the first 20 errors
                        self.stdout.write(f'  {error}')
                    if len(errors) > 20:
                        self.stdout.write(f'  ... dan {len(errors) - 20} error lainnya')

        except FileNotFoundError:
            raise CommandError(f'File tidak ditemukan: {csv_file}')
        except Exception as e:
            raise CommandError(f'Error membaca file CSV: {str(e)}')
