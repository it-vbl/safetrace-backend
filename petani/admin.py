from django.contrib import admin
from django import forms
from petani.models import Petani, Lampiran, Diklat, Pekerja
from utils.choices import JenisPekerjaan, JenisAPD
from wilayah_indonesia.forms import WilayahChainedFormMixin


class PetaniAdminForm(WilayahChainedFormMixin, forms.ModelForm):
    class Meta:
        model = Petani
        fields = (
            'id_petani', 'id_perbaikan', 'nama', 'nama_kelompok', 'jns_kelamin', 'no_ktp',
            'tempat', 'tanggal_lahir', 'alamat', 'no_kk', 'status_perkawinan', 'pendidikan_terakhir',
            'no_nib', 'tgl_terbit_sppl', 'no_wa', 'keanggotaan', 'tanggal_bergabung', 'tanggal_keluar',
            'provinsi', 'kabupaten', 'kecamatan', 'desa',
        )

@admin.register(Petani)
class PetaniAdmin(admin.ModelAdmin):
    list_display = ('id_petani', 'id_perbaikan', 'nama', 'nama_kelompok', 'jns_kelamin', 'no_ktp', 'alamat', 'provinsi', 'kabupaten',)
    search_fields = ('id_petani', 'id_perbaikan', 'nama', 'no_ktp', 'provinsi__nama', 'kabupaten__nama', 'kecamatan__nama', 'desa__nama',)
    list_filter = ('jns_kelamin', 'status_perkawinan', 'provinsi',)
    ordering = ('-created_at',)
    form = PetaniAdminForm


@admin.register(Lampiran)
class LampiranAdmin(admin.ModelAdmin):
    list_display = ('id', 'petani', 'file_ktp_check', 'file_kk_check', 'file_nib_check')
    search_fields = ('petani__nama', 'petani__id_perbaikan',)
    ordering = ('-created_at',)

    def file_ktp_check(self, obj):
        return bool(obj.file_ktp) 
    file_ktp_check.boolean = True
    file_ktp_check.short_description = "File KTP"
    
    def file_kk_check(self, obj):
        return bool(obj.file_kk) 
    file_kk_check.boolean = True
    file_kk_check.short_description = "File KK"
    
    def file_nib_check(self, obj):
        return bool(obj.file_nib) 
    file_nib_check.boolean = True
    file_nib_check.short_description = "File NIB"


@admin.register(Diklat)
class DiklatAdmin(admin.ModelAdmin):
    list_display = ('id', 'petani', 'file_sl_check', 'file_pnc_check', 'file_k3_check', 
                    'file_sop_check', 'file_fdg_check', 'pestisida')
    search_fields = ('petani__nama',)
    list_filter = ('sl', 'pnc', 'k3', 'sop', 'fdg', 'pestisida')
    ordering = ('-created_at',)
    
    def file_sl_check(self, obj):
        return bool(obj.sl) 
    file_sl_check.boolean = True
    file_sl_check.short_description = "SL"
    
    def file_pnc_check(self, obj):
        return bool(obj.pnc) 
    file_pnc_check.boolean = True
    file_pnc_check.short_description = "PNC"
    
    def file_k3_check(self, obj):
        return bool(obj.k3) 
    file_k3_check.boolean = True
    file_k3_check.short_description = "K3"
    
    def file_sop_check(self, obj):
        return bool(obj.sop) 
    file_sop_check.boolean = True
    file_sop_check.short_description = "SOP"
    
    def file_fdg_check(self, obj):
        return bool(obj.fdg) 
    file_fdg_check.boolean = True
    file_fdg_check.short_description = "FDG"
    
    def file_pestisida_check(self, obj):
        return bool(obj.pestisida) 
    file_pestisida_check.boolean = True
    file_pestisida_check.short_description = "Pestisida"


@admin.register(Pekerja)
class PekerjaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'nama', 'petani', 'jns_kelamin', 'no_ktp', 'status_pekerja',
        'jenis_pekerjaan_display', 'jenis_apd_display', 'file_ktp_check', 'file_kk_check'
    )
    search_fields = ('nama', 'petani__nama', 'petani__id_perbaikan', 'no_ktp',)
    list_filter = ('jns_kelamin', 'status_pekerja',)
    ordering = ('-created_at',)

    def file_ktp_check(self, obj):
        return bool(obj.file_ktp) 
    file_ktp_check.boolean = True
    file_ktp_check.short_description = "File KTP"
    
    def file_kk_check(self, obj):
        return bool(obj.file_kk) 
    file_kk_check.boolean = True
    file_kk_check.short_description = "File KK"

    def jenis_pekerjaan_display(self, obj):
        labels = dict(JenisPekerjaan.choices)
        return ', '.join(labels.get(choice, choice) for choice in obj.jenis_pekerjaan) if obj.jenis_pekerjaan else '-'
    jenis_pekerjaan_display.short_description = "Jenis Pekerjaan"

    def jenis_apd_display(self, obj):
        labels = dict(JenisAPD.choices)
        return ', '.join(labels.get(choice, choice) for choice in obj.jenis_apd) if obj.jenis_apd else '-'
    jenis_apd_display.short_description = "Jenis APD"
    