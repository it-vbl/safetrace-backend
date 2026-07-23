from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django import forms
from kebun.models import Kebun, Lampiran, KebunDeforestationAnalysis
from wilayah_indonesia.forms import WilayahChainedFormMixin


class KebunAdminForm(WilayahChainedFormMixin, forms.ModelForm):
    class Meta:
        model = Kebun
        fields = '__all__'

@admin.register(Kebun)
class KebunAdmin(GISModelAdmin):
    list_display = ('id_kebun', 'id_perbaikan', 'petani', 'lokasi_kebun', 'luas', 'is_rspo', 'is_ispo', 'jenis_legalitas', 'nomor_stdb')
    list_filter = ('jenis_legalitas', 'is_ispo', 'is_rspo')
    search_fields = ('id_kebun', 'id_perbaikan', 'petani__nama')
    ordering = ('-updated_at',)
    form = KebunAdminForm


@admin.register(Lampiran)
class LampiranAdmin(admin.ModelAdmin):
    list_display = ('id', 'kebun', 'file_legalitas_check', 'file_stdb_check', 
                    'file_rspo_check', 'file_ispo_check', 'file_gambar_peta_check')
    search_fields = ('kebun__id_kebun', 'kebun__id_perbaikan', 'kebun__petani__nama')
    ordering = ('-created_at',)

    def file_legalitas_check(self, obj):
        return bool(obj.file_legalitas) 
    file_legalitas_check.boolean = True
    file_legalitas_check.short_description = "File Legalitas"
    
    def file_stdb_check(self, obj):
        return bool(obj.file_stdb) 
    file_stdb_check.boolean = True
    file_stdb_check.short_description = "File STDB"
    
    def file_rspo_check(self, obj):
        return bool(obj.file_rspo) 
    file_rspo_check.boolean = True
    file_rspo_check.short_description = "File RSPO"
    
    def file_ispo_check(self, obj):
        return bool(obj.file_ispo) 
    file_ispo_check.boolean = True
    file_ispo_check.short_description = "File ISPO"
    
    def file_gambar_peta_check(self, obj):
        return bool(obj.file_gambar_peta)
    file_gambar_peta_check.boolean = True
    file_gambar_peta_check.short_description = "File Gambar Peta"


@admin.register(KebunDeforestationAnalysis)
class KebunDeforestationAnalysisAdmin(admin.ModelAdmin):
    list_display = ('kebun', 'whisp_status', 'last_updated')
    search_fields = ('kebun__id_kebun', 'kebun__id_perbaikan', 'kebun__petani__nama')
    ordering = ('-updated_at',)
    
    def last_updated(self, obj):
        return obj.updated_at
    last_updated.admin_order_field = 'updated_at'
    last_updated.short_description = 'Last Updated'
