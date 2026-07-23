from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Angkutan, KelompokPenyetor, Pabrik, Lampiran
from wilayah_indonesia.forms import WilayahChainedFormMixin


class PabrikAdminForm(WilayahChainedFormMixin, forms.ModelForm):
    class Meta:
        model = Pabrik
        fields = '__all__'


@admin.register(Angkutan)
class AngkutanAdmin(admin.ModelAdmin):
    list_display = [
        'no_registrasi', 
        'tanggal_penjualan', 
        'driver', 
        'no_polisi',
        'jumlah_tandan',
    ]
    
    search_fields = [
        'no_registrasi',
        'driver', 
        'no_polisi',
        'pabrik__nama'
    ]



@admin.register(KelompokPenyetor)
class KelompokPenyetorAdmin(admin.ModelAdmin):
    list_display = [
        'angkutan',
        'nama_kelompok',
        'jumlah_anggota',
        'anggota_preview',
        'total_penjualan_kelompok',
        'created_at_display',
        'updated_at_display'
    ]
    
    
    search_fields = [
        'nama_kelompok',
    ]
    
    ordering = ['-updated_at', 'nama_kelompok']
    
    readonly_fields = [
        'jumlah_anggota_display',
        'detail_anggota_display',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Detail Kelompok', {
            'fields': (
                'nama_kelompok',
                'anggota_petani',
            )
        }),
        ('Summary (Read Only)', {
            'fields': (
                'jumlah_anggota_display',
                'detail_anggota_display',
            ),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )
    
    filter_horizontal = ['anggota_petani']  # Better widget for ManyToMany
    
    list_per_page = 20
    
    actions = ['export_kelompok_summary']
    
    # Custom display methods
    def jumlah_anggota(self, obj):
        count = obj.anggota_petani.count()
        color = 'green' if count >= 5 else 'orange' if count >= 2 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} orang</span>',
            color,
            count
        )
    jumlah_anggota.short_description = 'Jumlah Anggota'
    
    def anggota_preview(self, obj):
        anggota = obj.anggota_petani.all()[:3]
        names = [a.nama for a in anggota]
        
        if obj.anggota_petani.count() > 3:
            names.append(f'... +{obj.anggota_petani.count() - 3} lainnya')
        
        return ', '.join(names)
    anggota_preview.short_description = 'Preview Anggota'
    
    def total_penjualan_kelompok(self, obj):
        """Calculate total sales from all group members"""
        try:
            total = 0
            for petani in obj.anggota_petani.all():
                # Take total sales from transports related to the farmer's kebun records
                kebun_petani = petani.petani.all()  # related_name from ForeignKey
                for kebun in kebun_petani:
                    angkutan = kebun.angkutan_penjualan.all()
                    total += sum(float(a.total_penjualan) for a in angkutan)
            
            if total > 0:
                return format_html(
                    '<span style="color: green; font-weight: bold;">Rp {:,.0f}</span>',
                    total
                )
            return 'Rp 0'
        except:
            return 'Error'
    total_penjualan_kelompok.short_description = 'Total Penjualan'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_at_display.short_description = 'Dibuat'
    created_at_display.admin_order_field = 'created_at'
    
    def updated_at_display(self, obj):
        return obj.updated_at.strftime('%d/%m/%Y %H:%M')
    updated_at_display.short_description = 'Diupdate'
    updated_at_display.admin_order_field = 'updated_at'
    
    # Read-only display fields
    def jumlah_anggota_display(self, obj):
        return f"{obj.anggota_petani.count()} orang"
    jumlah_anggota_display.short_description = 'Jumlah Anggota'
    
    def detail_anggota_display(self, obj):
        anggota_list = []
        for petani in obj.anggota_petani.all():
            kebun_count = petani.petani.count()  # Jumlah kebun petani
            anggota_list.append(f"• {petani.nama} ({kebun_count} kebun)")
        
        if anggota_list:
            return mark_safe('<br>'.join(anggota_list))
        return 'Tidak ada anggota'
    detail_anggota_display.short_description = 'Detail Anggota'
    
    # Custom actions
    def export_kelompok_summary(self, request, queryset):
        total_kelompok = queryset.count()
        total_anggota = sum(obj.anggota_petani.count() for obj in queryset)
        
        self.message_user(
            request,
            f"Summary: {total_kelompok} groups with a total of {total_anggota} members"
        )
    export_kelompok_summary.short_description = "Export kelompok summary"



@admin.register(Pabrik)
class PabrikAdmin(admin.ModelAdmin):
    list_display = ('nama', 'alamat', 'provinsi', 'kabupaten', 'kecamatan')
    search_fields = ('nama', 'alamat')
    form = PabrikAdminForm


@admin.register(Lampiran)
class LampiranAdmin(admin.ModelAdmin):
    list_display = ('angkutan', 'created_at', 'updated_at')
    search_fields = ('angkutan__no_registrasi', 'angkutan__driver')
    readonly_fields = ('created_at', 'updated_at')