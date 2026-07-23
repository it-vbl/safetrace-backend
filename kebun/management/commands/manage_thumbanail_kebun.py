from django.core.management.base import BaseCommand
from kebun.models import Lampiran


class Command(BaseCommand):
    help = 'Manage thumbnails for Lampiran models'
    
    def add_arguments(self, parser):
        parser.add_argument('action', choices=[
            'regenerate', 'cleanup', 'info', 'delete-all'
        ])
        parser.add_argument('--lampiran-id', type=int, help='Specific lampiran ID')
        parser.add_argument('--force', action='store_true', help='Force regeneration')
    
    def handle(self, *args, **options):
        action = options['action']
        lampiran_id = options.get('lampiran_id')
        force = options.get('force', False)
        
        if lampiran_id:
            try:
                lampiran = Lampiran.objects.get(id=lampiran_id)
                lampirans = [lampiran]
            except Lampiran.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Lampiran ID {lampiran_id} not found')
                )
                return
        else:
            lampirans = Lampiran.objects.all()
        
        if action == 'regenerate':
            for lampiran in lampirans:
                self.stdout.write(f'Regenerating thumbnails for Lampiran {lampiran.id}...')
                lampiran.regenerate_thumbnails()
            
            self.stdout.write(
                self.style.SUCCESS(f'Regenerated thumbnails for {len(lampirans)} lampirans')
            )
            
        elif action == 'cleanup':
            for lampiran in lampirans:
                lampiran.cleanup_orphaned_thumbnails()
            
            self.stdout.write(
                self.style.SUCCESS(f'Cleaned up thumbnails for {len(lampirans)} lampirans')
            )
            
        elif action == 'info':
            for lampiran in lampirans:
                info = lampiran.get_thumbnail_info()
                self.stdout.write(f'\nLampiran {lampiran.id}:')
                for field, data in info.items():
                    self.stdout.write(f'  {field}:')
                    for key, value in data.items():
                        color = self.style.SUCCESS if value else self.style.WARNING
                        self.stdout.write(f'    {key}: {color(value)}')
                        
        elif action == 'delete-all':
            for lampiran in lampirans:
                lampiran.delete_all_thumbnails()
            
            self.stdout.write(
                self.style.SUCCESS(f'Deleted all thumbnails for {len(lampirans)} lampirans')
            )