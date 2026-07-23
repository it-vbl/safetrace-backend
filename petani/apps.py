from django.apps import AppConfig


class PetaniConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'petani'

    def ready(self):
        import petani.signals
