import csv
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from petani.models import Petani
from utils.choices import StatusKeanggotaan


class Command(BaseCommand):
    help = 'Import data keanggotaan petani (tanggal bergabung dan keluar) dari file CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path ke file CSV')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Jalankan tanpa menyimpan data (testing mode)',
        )

    def parse_date(self, date_str):
        """Parse a date in DD-MM-YYYY, MM-DD-YYYY, DD/MM/YY, or DD/MM/YYYY format"""
        if not date_str or not date_str.strip():
            return None
        
        date_str = date_str.strip()
        
        # List of supported formats to try
        formats = [
            '%d-%m-%Y',    # DD-MM-YYYY
            '%m-%d-%Y',    # MM-DD-YYYY (American format)
            '%d/%m/%y',    # DD/MM/YY
            '%d/%m/%Y',    # DD/MM/YYYY
            '%m/%d/%Y',    # MM/DD/YYYY (American format)
        ]
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.date()
            except ValueError:
                continue
        
        # If none of the formats worked, raise an error
        raise ValueError(f"Format tanggal tidak valid: {date_str}")

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - data will not be saved'))

        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file, delimiter=';')
                
                success_count = 0
                skip_count = 0
                error_count = 0
                errors = []
                keluar_count = 0  # Counter for farmers who leave

                with transaction.atomic():
                    for row_num, row in enumerate(csv_reader, start=2):
                        try:
                            # Get id_petani
                            id_petani = row.get('id_petani', '').strip()
                            if not id_petani:
                                skip_count += 1
                                self.stdout.write(
                                    self.style.WARNING(f"⊘ Baris {row_num}: Tidak ada id_petani, dilewati")
                                )
                                continue

                            # Find the farmer by id_petani
                            try:
                                petani = Petani.objects.get(id_petani=id_petani)
                            except Petani.DoesNotExist:
                                skip_count += 1
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"⊘ Baris {row_num}: Petani dengan ID '{id_petani}' tidak ditemukan, dilewati"
                                    )
                                )
                                continue

                            # Parse join date
                            tgl_masuk_str = row.get('tgl_masuk', '').strip()
                            try:
                                tanggal_bergabung = self.parse_date(tgl_masuk_str)
                            except ValueError as e:
                                raise ValueError(f"Tanggal masuk error: {str(e)}")

                            # Parse leave date
                            tgl_keluar_str = row.get('tgl_keluar', '').strip()
                            try:
                                tanggal_keluar = self.parse_date(tgl_keluar_str)
                            except ValueError as e:
                                raise ValueError(f"Tanggal keluar error: {str(e)}")

                            # Determine membership status
                            # If a leave date exists, membership becomes inactive
                            keanggotaan = StatusKeanggotaan.AKTIF if tanggal_keluar is None else StatusKeanggotaan.TIDAK_AKTIF

                            # Update farmer data
                            if not dry_run:
                                petani.tanggal_bergabung = tanggal_bergabung
                                petani.tanggal_keluar = tanggal_keluar
                                petani.keanggotaan = keanggotaan
                                petani.save()

                            success_count += 1
                            if keanggotaan == StatusKeanggotaan.TIDAK_AKTIF:
                                keluar_count += 1

                            # Build the status string
                            status_parts = []
                            if tanggal_bergabung:
                                status_parts.append(f"Masuk: {tanggal_bergabung.strftime('%d/%m/%Y')}")
                            if tanggal_keluar:
                                status_parts.append(f"Keluar: {tanggal_keluar.strftime('%d/%m/%Y')}")
                            
                            status_str = " | ".join(status_parts) if status_parts else "Tidak ada tanggal"
                            keanggotaan_str = "Non-Aktif" if not keanggotaan else "Aktif"
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✓ Baris {row_num}: {petani.nama} ({id_petani}) - {keanggotaan_str} | {status_str}"
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
                self.stdout.write(self.style.WARNING(f'Dilewati: {skip_count} record'))
                self.stdout.write(self.style.ERROR(f'Gagal: {error_count} record'))
                self.stdout.write(self.style.NOTICE(f'Petani Keluar (Non-Aktif): {keluar_count} record'))
                self.stdout.write(self.style.NOTICE(f'Petani Aktif: {success_count - keluar_count} record'))
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('\n⚠ DRY RUN MODE - Tidak ada data yang disimpan'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'\n✓ Import selesai! Total {success_count} data keanggotaan berhasil diupdate'))

                if errors:
                    self.stdout.write('\n' + self.style.ERROR('Daftar error:'))
                    for error in errors[:20]:
                        self.stdout.write(f'  {error}')
                    if len(errors) > 20:
                        self.stdout.write(f'  ... dan {len(errors) - 20} error lainnya')

        except FileNotFoundError:
            raise CommandError(f'File tidak ditemukan: {csv_file}')
        except Exception as e:
            raise CommandError(f'Error membaca file CSV: {str(e)}')
