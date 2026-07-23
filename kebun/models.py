import logging
from datetime import datetime
from django.contrib.gis.db import models
from utils.choices import (
    JenisLegalitas, WHISPStatus, KomoditasKelembagaan, PolaTanam, JenisLahan,
    AsalBenih, JenisPupuk
)
from utils.thumbnails import ThumbnailsMixin
from utils.validators import MaxSizeFileValidator
from wilayah_indonesia.models import WilayahDisplayMixin

logger = logging.getLogger(__name__)

class Kebun(WilayahDisplayMixin, models.Model):
    id_kebun = models.CharField(max_length=100, unique=True, db_index=True)
    id_perbaikan = models.CharField(max_length=100, blank=True, null=True, help_text='ID Perbaikan dari Lembaga')
    petani = models.ForeignKey('petani.Petani', on_delete=models.CASCADE)
    lokasi_kebun = models.CharField(max_length=100, help_text='Nama lokasi atau daerah kebun')
    luas = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text='Luas (Ha)')
    luas_peta = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text='Luas (Ha)')
    waktu_tanam = models.DateField(help_text='Bulan dan Tahun', blank=True, null=True)
    jumlah_pokok = models.IntegerField()
    is_rspo = models.BooleanField(default=False, help_text='Sudah RSPO')
    is_ispo = models.BooleanField(default=False, help_text='Sudah ISPO')
    jenis_legalitas = models.CharField(blank=True, null=True, max_length=2, choices=JenisLegalitas.choices)
    nomor_legalitas = models.CharField(blank=True, null=True, max_length=50)
    pemilik_legalitas = models.CharField(blank=True, null=True, max_length=100)
    jenis_bibit = models.CharField(blank=True, null=True, max_length=50)
    nomor_stdb = models.CharField(blank=True, null=True, max_length=100)
    titik_koordinat = models.PointField(blank=True, null=True, help_text="Koordinat kebun")
    geom = models.PolygonField(blank=True, null=True, help_text="Peta Kebun", srid=4326)
    
    # stdb support fields
    komoditas = models.CharField(blank=True, null=True, max_length=50, choices=KomoditasKelembagaan.choices)
    pola_tanam = models.CharField(blank=True, null=True, max_length=50, choices=PolaTanam.choices)
    jenis_lahan = models.CharField(blank=True, null=True, max_length=50, choices=JenisLahan.choices)
    asal_benih = models.CharField(blank=True, null=True, max_length=50, choices=AsalBenih.choices)
    jenis_pupuk = models.CharField(blank=True, null=True, max_length=50, choices=JenisPupuk.choices)
    tahun_peremajaan = models.IntegerField(blank=True, null=True, help_text="Tahun peremajaan terakhir")
    jumlah_pohon = models.IntegerField(blank=True, null=True, help_text="Jumlah pohon di kebun")
    total_prod_per_tahun = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, help_text="Total produksi per tahun dalam (kg)")
    mitra_penjualan = models.CharField(blank=True, null=True, max_length=100, help_text="Mitra penjualan hasil panen")
    
    # Wilayah administratif
    provinsi = models.ForeignKey("wilayah_indonesia.Provinsi", on_delete=models.SET_NULL, null=True, blank=True)
    kabupaten = models.ForeignKey("wilayah_indonesia.Kabupaten", on_delete=models.SET_NULL, null=True, blank=True)
    kecamatan = models.ForeignKey("wilayah_indonesia.Kecamatan", on_delete=models.SET_NULL, null=True, blank=True)
    desa = models.ForeignKey("wilayah_indonesia.Desa", on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.id_kebun} - {self.petani}"
    
    @property
    def get_tahun_tanam(self):
        if self.waktu_tanam:
            return self.waktu_tanam.year
        return None
    
    # Start: Method relasi ke model GAP Produksi
    def get_umur_tanaman(self):
        if self.waktu_tanam:
            current = datetime.now().date()
            delta = current - self.waktu_tanam
            try:
                years = delta.days / 365
                return years
            except ZeroDivisionError:
                return 0
        return 0
    
    def get_total_produksi_gap(self, tahun=None):
        total = 0
        if tahun:
            produksis = self.produksi_set.filter(tahun=tahun)
        else:
            produksis = self.produksi_set.all()
                
        for produksi in produksis:
            total += produksi.get_total_produksi()
        return total

    def get_prod_ha_year_gap(self, tahun=None):
        from decimal import Decimal
        luas = self.luas
        produksi = self.get_total_produksi_gap(tahun)
        return round(produksi / Decimal(str(luas)), 3) if luas > 0 else 0
    # End: Method relasi ke model GAP Produksi
    
    # Start: Method relasi ke model GAP Pestisida
    def get_total_pestisida_gap(self, tahun=None):
        total = 0
        if tahun:
            pestisidas = self.penggunaan_pestisida.filter(tahun=tahun)
        else:
            pestisidas = self.penggunaan_pestisida.all()
        
        for pestisida in pestisidas:
            total += pestisida.total_pestisida if pestisida.total_pestisida else 0
        return total
    # end: Method relasi ke model GAP Pestisida
    
    # Start: Method relasi ke model GAP LB3
    def get_total_lb3_gap(self, tahun=None):
        total = 0
        if tahun:
            lb3s = self.lb3_set.filter(tahun=tahun)
        else:
            lb3s = self.lb3_set.all()
        
        for lb3 in lb3s:
            total += lb3.total_lb3 if lb3.total_lb3 else 0
        return total
    # end: Method relasi ke model GAP LB3
    
    # Start: Method relasi ke model GAP Pupuk
    def get_total_pupuk_gap(self, tahun=None):
        total = 0
        if tahun:
            pupuks = self.penggunaan_pupuk.filter(tahun=tahun)
        else:
            pupuks = self.penggunaan_pupuk.all()
        
        for pupuk in pupuks:
            total += pupuk.total_pupuk if pupuk.total_pupuk else 0
        return total
    # end: Method relasi ke model GAP Pupuk
    
    @property
    def centroid_point(self):
        if self.geom:
            centroid = self.geom.centroid
            return {
                "type": "Point",
                "coordinates": [centroid.x, centroid.y]
            }
        return None

    @property
    def get_waktu_tanam(self):
        return self.waktu_tanam.strftime("%B %Y") if self.waktu_tanam else None

    @property
    def luas_area_geom(self):
        if self.geom:
            # Luas dalam satuan meter persegi
            area_m2 = self.geom.transform(3857, clone=True).area
            # Konversi ke hektar (1 hektar = 10_000 m2)
            return round(area_m2 / 10000, 3)
        return 0
    
    @property
    def risk_acrop(self):
        """
        'risk_acrop': {
            'low': 'Area aman dari tekanan konversi ke pertanian pangan',
            'medium': 'Ada potensi tekanan konversi, perlu monitoring',
            'high': 'Risiko tinggi konversi ke lahan pertanian'
        }
        """
        if hasattr(self, 'deforestation_analysis') and self.deforestation_analysis.whisp_analysis:
            try:
                return self.deforestation_analysis \
                    .whisp_analysis['data']['data']['features'][0]['properties']['risk_acrop']
            except Exception as e:
                return ""
        return ""
    
    @property
    def risk_pcrop(self):
        """
        'risk_pcrop': {
            'low': 'Area stabil, tidak ada tekanan ekspansi perkebunan baru',
            'medium': 'Ada potensi ekspansi perkebunan di sekitar area',
            'high': 'Risiko tinggi konversi hutan untuk perkebunan baru'
        }
        """
        if hasattr(self, 'deforestation_analysis') and self.deforestation_analysis.whisp_analysis:
            try:
                return self.deforestation_analysis \
                    .whisp_analysis['data']['data']['features'][0]['properties']['risk_pcrop']
            except Exception as e:
                return ""
        return ""
    
    @property
    def risk_timber(self):
        """
        'risk_timber': {
            'low': 'Area aman dari aktivitas illegal logging',
            'medium': 'Perlu waspada terhadap aktivitas penebangan',
            'high': 'Risiko tinggi illegal logging di area sekitar'
        }
        """
        if hasattr(self, 'deforestation_analysis') and self.deforestation_analysis.whisp_analysis:
            try:
                return self.deforestation_analysis \
                    .whisp_analysis['data']['data']['features'][0]['properties']['risk_timber']
            except Exception as e:
                return ""
        return ""
    
    @property
    def whisp_properties(self):
        if hasattr(self, 'deforestation_analysis') and self.deforestation_analysis.whisp_analysis:
            try:
                return self.deforestation_analysis.whisp_analysis['data']['data']['features'][0]['properties']
            except Exception as e:
                return {}
        return {}

    def save(self, *args, **kwargs):
        if self.geom:
            self.titik_koordinat = self.geom.centroid
            self.luas = self.luas_area_geom
        return super().save(*args, **kwargs)


class Lampiran(ThumbnailsMixin, models.Model):
    kebun = models.OneToOneField(Kebun, on_delete=models.CASCADE)
    file_legalitas = models.FileField(
        upload_to='legalitas/', 
        null=True, 
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_legalitas = models.ImageField(upload_to='thumbs/legalitas/', null=True, blank=True)
    file_stdb = models.FileField(
        upload_to='stdb/', 
        null=True, 
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_stdb = models.ImageField(upload_to='thumbs/stdb/', null=True, blank=True)
    file_rspo = models.FileField(
        upload_to='rspo/', 
        null=True, 
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_rspo = models.ImageField(upload_to='thumbs/rspo/', null=True, blank=True)
    file_ispo = models.FileField(
        upload_to='ispo/', 
        null=True, 
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_ispo = models.ImageField(upload_to='thumbs/ispo/', null=True, blank=True)
    file_gambar_peta = models.FileField(
        upload_to='gambar_peta/',
        null=True,
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_gambar_peta = models.ImageField(upload_to='thumbs/gambar_peta/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"lampiran: {self.kebun}"
    
    def _get_mapping_field_names(self):
        return {
            'file_legalitas': 'thumb_legalitas',
            'file_stdb': 'thumb_stdb', 
            'file_rspo': 'thumb_rspo',
            'file_ispo': 'thumb_ispo',
            'file_gambar_peta': 'thumb_gambar_peta',
        }

class KebunDeforestationAnalysis(models.Model):
    kebun = models.OneToOneField(Kebun, on_delete=models.CASCADE, related_name='deforestation_analysis')
    whisp_analysis = models.JSONField(
        null=True, 
        blank=True, 
        help_text="Hasil analisis WHISP untuk geometri kebun"
    )
    whisp_status = models.CharField(
        max_length=20,
        choices=WHISPStatus.choices,
        default=WHISPStatus.PENDING,
        help_text="Status analisis WHISP"
    )
    whisp_job_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID job RQ untuk tracking"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Deforestation {self.kebun.id_kebun}"