from django.apps import AppConfig


class KebunConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kebun'
    
    def ready(self):
        import kebun.signals
