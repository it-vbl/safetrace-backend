import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from petani.models import Petani, Diklat


class Command(BaseCommand):
    help = 'Import data diklat petani dari file CSV'

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

        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file, delimiter=';')
                
                success_count = 0
                skip_count = 0
                error_count = 0
                errors = []

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

                            # Parse boolean fields
                            # If the value is '1', treat it as True; otherwise False
                            sl = row.get('sl', '').strip() == '1'
                            pnc = row.get('pnc', '').strip() == '1'
                            pestisida = row.get('pestisida', '').strip() == '1'
                            k3 = row.get('k3', '').strip() == '1'
                            sop = row.get('sop', '').strip() == '1'
                            
                            # Handle fdg or pdg (a typo in the CSV or model)
                            fdg_value = row.get('fdg', '').strip()
                            pdg_value = row.get('pdg', '').strip()
                            fdg = (fdg_value == '1') or (pdg_value == '1')

                            # Prepare diklat data
                            diklat_data = {
                                'sl': sl,
                                'pnc': pnc,
                                'pestisida': pestisida,
                                'k3': k3,
                                'sop': sop,
                                'fdg': fdg,
                            }

                            if not dry_run:
                                # get_or_create Diklat
                                diklat, created = Diklat.objects.get_or_create(
                                    petani=petani,
                                    defaults=diklat_data
                                )
                                
                                # If it already exists, update the data
                                if not created:
                                    for key, value in diklat_data.items():
                                        setattr(diklat, key, value)
                                    diklat.save()
                                    action = "diupdate"
                                else:
                                    action = "dibuat"
                            else:
                                # Check whether it already exists for reporting
                                existing = Diklat.objects.filter(petani=petani).exists()
                                action = "akan diupdate" if existing else "akan dibuat"
                            
                            success_count += 1
                            
                            # Build the diklat info string
                            diklat_info = []
                            if sl: diklat_info.append("SL")
                            if pnc: diklat_info.append("PNC")
                            if pestisida: diklat_info.append("Pestisida")
                            if k3: diklat_info.append("K3")
                            if sop: diklat_info.append("SOP")
                            if fdg: diklat_info.append("FDG")
                            
                            diklat_str = ", ".join(diklat_info) if diklat_info else "Tidak ada"
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✓ Baris {row_num}: {petani.nama} ({id_petani}) - {action} | Diklat: {diklat_str}"
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
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('\n⚠ DRY RUN MODE - Tidak ada data yang disimpan'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'\n✓ Import selesai! Total {success_count} data diklat berhasil diproses'))

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
