from django.contrib import admin
from gap.models import Produksi, LB3, Pupuk, PenggunaanPestisida, PenggunaanPupuk


@admin.register(Produksi)
class ProduksiAdmin(admin.ModelAdmin):
    list_display = ('id', 'tahun', 'kebun__petani__nama')
    search_fields = ('tahun', 'kebun__petani__nama')
    list_filter = ('tahun',)


@admin.register(LB3)
class LB3Admin(admin.ModelAdmin):
    list_display = ('id', 'tahun', 'kebun__petani__nama', 'limbah_bobot', 'limbah_jeriken', 'limbah_karung_pupuk')
    search_fields = ('tahun', 'kebun__petani__nama')
    list_filter = ('tahun',)


# @admin.register(Pupuk)
# class PupukAdmin(admin.ModelAdmin):
#     list_display = ('id', 'tahun', 'kebun__petani__nama', 'semester')
#     search_fields = ('tahun', 'kebun__petani__nama')
#     list_filter = ('tahun', 'semester')


@admin.register(PenggunaanPestisida)
class PenggunaanPestisidaAdmin(admin.ModelAdmin):
    list_display = ('id', 'tahun', 'kebun__petani__nama')
    search_fields = ('tahun', 'kebun__petani__nama')
    list_filter = ('tahun',)


@admin.register(PenggunaanPupuk)
class PenggunaanPupukAdmin(admin.ModelAdmin):
    list_display = ('id', 'tahun', 'kebun__petani__nama')
    search_fields = ('tahun', 'kebun__petani__nama')
    list_filter = ('tahun',)
