from django.apps import AppConfig


class PenjualanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'penjualan'

    def ready(self):
        import penjualan.signals
