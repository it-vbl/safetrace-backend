from django.contrib.gis import admin
from layer_static.models import LayerStatic
from adminsortable2.admin import SortableAdminMixin


@admin.register(LayerStatic)
class StaticLayerAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "order", "is_active")
    search_fields = ("name",)
