from django.contrib.gis import admin
from .models import AdmDesaArea, DeforeStation


@admin.register(AdmDesaArea)
class AdmDesaAreaAdmin(admin.GISModelAdmin):
    list_display = ('desa', 'kecamatan', 'kabupaten', 'provinsi')
    search_fields = ('desa', 'kecamatan', 'kabupaten', 'provinsi')
    
    
@admin.register(DeforeStation)
class DeforeStationAdmin(admin.GISModelAdmin):
    list_display = ('label', 'date', 'source_type', 'area_ha', 'created_at', 'updated_at')
    search_fields = ('id', 'label', 'source_type')
    list_filter = ('source_type', 'date', 'created_at')

