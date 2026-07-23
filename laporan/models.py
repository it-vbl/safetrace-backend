from django.db import models
from petani.models import Petani
from utils.choices import StatusSTDB


MONTH_CHOICES = [
    (1, 'Januari'),
    (2, 'Februari'),
    (3, 'Maret'),
    (4, 'April'),
    (5, 'Mei'),
    (6, 'Juni'),
    (7, 'Juli'),
    (8, 'Agustus'),
    (9, 'September'),
    (10, 'Oktober'),
    (11, 'November'),
    (12, 'Desember'),
]


class LaporanStatistik(models.Model):
    bulan = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    tahun = models.PositiveSmallIntegerField()
    judul = models.CharField(max_length=255)
    kebutuhan = models.TextField()
    file_excel = models.FileField(upload_to='laporan/', null=True, blank=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='laporan_statistik_created')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Laporan Statistik'
        verbose_name_plural = 'Laporan Statistik'
        ordering = ['-tahun', '-bulan']

    def __str__(self):
        return self.judul


class LaporanPetani(models.Model):
    petani = models.ForeignKey(Petani, on_delete=models.CASCADE, related_name='laporan')
    judul = models.CharField(max_length=255)
    kebutuhan = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Laporan Petani'
        verbose_name_plural = 'Laporan Petani'
        ordering = ['-created_at']

    def __str__(self):
        return self.judul


class LaporanSTDB(models.Model):
    status = models.CharField(max_length=20, choices=StatusSTDB.choices)
    judul = models.CharField(max_length=255)
    kebutuhan = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Laporan STDB'
        verbose_name_plural = 'Laporan STDB'
        ordering = ['-created_at']

    def __str__(self):
        return self.judul

