from django.db import models
from datetime import date
from utils.choices import (
    JenisKelamin, StatusPerkawinan, StatusPekerja, SumberKontak, StatusKeanggotaan,
    PendidikanTerakhir, JenisPekerjaan, JenisAPD
)
from utils.fields import ChoiceArrayField
from utils.validators import validate_indonesian_phone_number, MaxSizeFileValidator
from utils.thumbnails import ThumbnailsMixin
from django.db.models import Sum


class Petani(models.Model):
    id_petani = models.CharField(unique=True, max_length=50, db_index=True)
    id_perbaikan = models.CharField(max_length=100, blank=True, null=True, help_text='ID Perbaikan dari Lembaga terkait')
    nama = models.CharField(max_length=100)
    nama_kelompok = models.CharField(max_length=100, db_index=True)
    jns_kelamin = models.CharField(max_length=10, choices=JenisKelamin.choices)
    no_ktp = models.CharField(max_length=30, db_index=True)
    tempat = models.CharField(max_length=100, blank=True, null=True)
    tanggal_lahir = models.DateField(blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    no_kk = models.CharField(max_length=20, blank=True, null=True)
    status_perkawinan = models.CharField(max_length=2, choices=StatusPerkawinan.choices, blank=True, null=True)
    pendidikan_terakhir = models.CharField(max_length=100, blank=True, null=True, choices=PendidikanTerakhir.choices)
    no_nib = models.CharField(max_length=50, blank=True, null=True)
    tgl_terbit_sppl = models.DateField(blank=True, null=True)
    no_wa = models.CharField(max_length=20, blank=True, null=True, validators=[validate_indonesian_phone_number])
    keanggotaan = models.CharField(max_length=1, choices=StatusKeanggotaan.choices, 
                                   default=StatusKeanggotaan.AKTIF, help_text="Status keanggotaan petani")
    tanggal_bergabung = models.DateField(blank=True, null=True, help_text="Tanggal petani bergabung ke kelompok")
    tanggal_keluar = models.DateField(blank=True, null=True, help_text="Tanggal petani keluar dari kelompok")
    
    provinsi = models.ForeignKey("wilayah_indonesia.Provinsi", on_delete=models.SET_NULL, null=True, blank=True)
    kabupaten = models.ForeignKey("wilayah_indonesia.Kabupaten", on_delete=models.SET_NULL, null=True, blank=True)
    kecamatan = models.ForeignKey("wilayah_indonesia.Kecamatan", on_delete=models.SET_NULL, null=True, blank=True)
    desa = models.ForeignKey("wilayah_indonesia.Desa", on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nama

    def get_luas_kebun(self):
        total_luas = self.kebun_set.aggregate(Sum('luas'))['luas__sum']
        return total_luas or 0
    
    def save(self, *args, **kwargs):
        petani = super().save(*args, **kwargs)
        return petani
    
    def get_jumlah_kebun(self):
        return self.kebun_set.count()

    def get_umur(self):
        if not self.tanggal_lahir:
            return None

        today = date.today()
        return today.year - self.tanggal_lahir.year - (
            (today.month, today.day) < (self.tanggal_lahir.month, self.tanggal_lahir.day)
        )


class Lampiran(ThumbnailsMixin, models.Model):
    petani = models.OneToOneField(Petani, on_delete=models.CASCADE)
    file_ktp = models.FileField(
        upload_to='ktp/', 
        null=True, 
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_ktp = models.ImageField(upload_to='thumbs/ktp/', null=True, blank=True)
    file_kk = models.FileField(
        upload_to='kk/', 
        null=True, 
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_kk = models.ImageField(upload_to='thumbs/kk/', null=True, blank=True)
    file_nib = models.FileField(
        upload_to='nib/', 
        null=True, 
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_nib = models.ImageField(upload_to='thumbs/nib/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"lampiran: {self.petani}"

    def _get_mapping_field_names(self):
        return {
            'file_ktp': 'thumb_ktp',
            'file_kk': 'thumb_kk', 
            'file_nib': 'thumb_nib'
        }


class Diklat(models.Model):
    petani = models.OneToOneField(Petani, on_delete=models.CASCADE)
    sl = models.BooleanField(default=False, help_text="Sertifikasi Lainnya")
    sl_trainer = models.CharField(max_length=100, blank=True, null=True, 
                                  help_text="Nama trainer Sertifikasi Lainnya")
    pnc = models.BooleanField(default=False, help_text="RSPO/ISPO")
    pnc_trainer = models.CharField(max_length=100, blank=True, null=True, 
                                   help_text="Nama trainer RSPO/ISPO")
    k3 = models.BooleanField(default=False, help_text="Kesehatan dan Keselamatan Kerja")
    k3_trainer = models.CharField(max_length=100, blank=True, null=True, 
                                  help_text="Nama trainer Kesehatan dan Keselamatan Kerja")
    sop = models.BooleanField(default=False, help_text="Standar Operasional Prosedur")
    sop_trainer = models.CharField(max_length=100, blank=True, null=True, 
                                   help_text="Nama trainer Standar Operasional Prosedur")
    fdg = models.BooleanField(default=False, help_text="Pengendalian Diri dan Gizi")
    fdg_trainer = models.CharField(max_length=100, blank=True, null=True, 
                                   help_text="Nama trainer Pengendalian Diri dan Gizi")
    pestisida = models.BooleanField(default=False, help_text="Penggunaan Pestisida")
    pestisida_trainer = models.CharField(max_length=100, blank=True, null=True, 
                                         help_text="Nama trainer Penggunaan Pestisida")
    manajemen_api = models.BooleanField(default=False, help_text="Manajemen Api")
    manajemen_api_trainer = models.CharField(max_length=100, blank=True, null=True, 
                                             help_text="Nama trainer Manajemen Api")
    pengendalian_hpt = models.BooleanField(default=False, help_text="Pengendalian Hama dan Penyakit Tanaman")
    pengendalian_hpt_trainer = models.CharField(max_length=100, blank=True, null=True, 
                                                help_text="Nama trainer Pengendalian Hama dan Penyakit Tanaman")
    nkt = models.BooleanField(default=False, help_text="Nilai Konservasi Tinggi")
    nkt_trainer = models.CharField(max_length=100, blank=True, null=True, 
                                   help_text="Nama trainer Nilai Konservasi Tinggi")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"diklat: {self.petani}"


class Pekerja(ThumbnailsMixin, models.Model):
    petani = models.ForeignKey(Petani, on_delete=models.CASCADE, related_name='pekerja')
    nama = models.CharField(max_length=100)
    jns_kelamin = models.CharField(max_length=10, choices=JenisKelamin.choices, blank=True, null=True)
    kelompok_tani = models.CharField(max_length=100, blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    no_ktp = models.CharField(max_length=20, blank=True, null=True)
    tempat_lahir = models.CharField(max_length=100, blank=True, null=True)
    tanggal_lahir = models.DateField(blank=True, null=True)
    no_kk = models.CharField(max_length=20, blank=True, null=True)
    no_wa = models.CharField(max_length=20, blank=True, null=True, validators=[validate_indonesian_phone_number])
    status_pekerja = models.CharField(max_length=20, blank=True, null=True, choices=StatusPekerja.choices)
    jenis_pekerjaan = ChoiceArrayField(
        models.CharField(max_length=2, choices=JenisPekerjaan.choices),
        blank=True,
        default=list,
    )
    jenis_apd = ChoiceArrayField(
        models.CharField(max_length=2, choices=JenisAPD.choices),
        blank=True,
        default=list,
    )
    file_ktp = models.FileField(upload_to='pekerja-ktp/', null=True, blank=True)
    thumb_ktp = models.ImageField(upload_to='thumbs/ktp/', null=True, blank=True)
    file_kk = models.FileField(upload_to='pekerja-kk/', null=True, blank=True)
    thumb_kk = models.ImageField(upload_to='thumbs/kk/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"pekerja: {self.nama} - {self.petani}"

    def get_umur(self):
        if not self.tanggal_lahir:
            return None

        today = date.today()
        return today.year - self.tanggal_lahir.year - (
            (today.month, today.day) < (self.tanggal_lahir.month, self.tanggal_lahir.day)
        )
    
    def _get_mapping_field_names(self):
        return {
            'file_ktp': 'thumb_ktp',
            'file_kk': 'thumb_kk',
        }