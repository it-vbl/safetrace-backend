from django.db import models
from utils.thumbnails import ThumbnailsMixin
from utils.validators import MaxSizeFileValidator
from wilayah_indonesia.models import WilayahDisplayMixin, Provinsi, Kabupaten, Kecamatan


class Pabrik(WilayahDisplayMixin, models.Model):
    nama = models.CharField(max_length=200, db_index=True, help_text="Nama Pabrik Tujuan Penjualan")
    provinsi = models.ForeignKey(Provinsi, on_delete=models.SET_NULL, null=True, blank=True)
    kabupaten = models.ForeignKey(Kabupaten, on_delete=models.SET_NULL, null=True, blank=True)
    kecamatan = models.ForeignKey(Kecamatan, on_delete=models.SET_NULL, null=True, blank=True)
    alamat = models.TextField(help_text="Alamat lengkap pabrik", blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pabrik"
        verbose_name_plural = "Pabrik"
        ordering = ['nama']
    
    def __str__(self):
        return self.nama


class Angkutan(models.Model):
    # Detail Angkutan
    tanggal_penjualan = models.DateField(
        help_text="Tanggal penjualan TBS"
    )
    driver = models.CharField(
        max_length=100,
        help_text="Nama driver angkutan"
    )
    no_registrasi = models.CharField(
        max_length=50,
        unique=True,
        help_text="Nomor registrasi angkutan"
    )
    
    # Detail Polisi dan Angkutan
    no_polisi = models.CharField(
        max_length=20,
        help_text="Nomor polisi kendaraan"
    )
    jumlah_tandan = models.IntegerField(
        default=0,
        help_text="Jumlah tandan TBS"
    )
    berat_timbangan = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Berat timbangan dalam Kg"
    )
    
    # Detail Tarra dan Potongan
    tarra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Berat tarra dalam Kg"
    )
    t_potongan_persen = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Persentase potongan tarra (%)"
    )
    t_potongan_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Potongan tarra dalam Kg"
    )
    
    # Detail Berat dan Penjualan
    berat_bersih = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Berat bersih TBS dalam Kg"
    )
    harga_per_kilo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Harga per kilogram dalam Rupiah"
    )
    total_penjualan = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total penjualan dalam Rupiah"
    )
    
    pabrik = models.ForeignKey(
        Pabrik,
        on_delete=models.SET_NULL,
        related_name='angkutan_penjualan',
        null=True,
        blank=True,
        help_text="Pabrik tujuan penjualan"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Angkutan"
        verbose_name_plural = "Angkutan"
        ordering = ['-tanggal_penjualan', '-created_at']
        indexes = [
            models.Index(fields=['tanggal_penjualan']),
            models.Index(fields=['no_registrasi']),
            models.Index(fields=['driver']),
        ]
    
    def __str__(self):
        return f"{self.no_registrasi} - {self.driver} ({self.tanggal_penjualan})"
    
    @property
    def total_potongan(self):
        """Total deduction (tara + tara deduction)"""
        return float(self.tarra) + float(self.t_potongan_kg)
    
    @property
    def persentase_potongan_total(self):
        """Percentage of total deduction relative to weighed weight"""
        if self.berat_timbangan > 0:
            return round((self.total_potongan / float(self.berat_timbangan)) * 100, 2)
        return 0
    
    @property
    def rata_rata_berat_per_tandan(self):
        """Average weight per bunch"""
        if self.jumlah_tandan > 0:
            return round(float(self.berat_bersih) / self.jumlah_tandan, 2)
        return 0
    
    def get_profit_margin(self, harga_beli_per_kg=None):
        """Calculate profit margin if a purchase price is available"""
        if harga_beli_per_kg and self.harga_per_kilo > harga_beli_per_kg:
            profit_per_kg = float(self.harga_per_kilo) - float(harga_beli_per_kg)
            total_profit = profit_per_kg * float(self.berat_bersih)
            return {
                'profit_per_kg': profit_per_kg,
                'total_profit': total_profit,
                'profit_margin_persen': round((profit_per_kg / float(self.harga_per_kilo)) * 100, 2)
            }
        return None
    
    def get_summary(self):
        """Get summary data for reporting"""
        return {
            'no_registrasi': self.no_registrasi,
            'tanggal': self.tanggal_penjualan.strftime('%d-%m-%Y'),
            'driver': self.driver,
            'berat_kotor': float(self.berat_timbangan),
            'total_potongan': self.total_potongan,
            'berat_bersih': float(self.berat_bersih),
            'jumlah_tandan': self.jumlah_tandan,
            'rata_rata_per_tandan': self.rata_rata_berat_per_tandan,
            'harga_per_kg': float(self.harga_per_kilo),
            'total_penjualan': float(self.total_penjualan),
            'kebun': self.kebun.id_kebun if self.kebun else None,
            'petani': self.kebun.petani.nama if self.kebun and self.kebun.petani else None
        }

    @classmethod
    def get_monthly_summary(cls, year, month):
        """Get monthly sales summary"""
        angkutan = cls.objects.filter(
            tanggal_penjualan__year=year,
            tanggal_penjualan__month=month
        )
        
        if not angkutan.exists():
            return None
        
        total_tandan = sum(a.jumlah_tandan for a in angkutan)
        total_berat_kotor = sum(float(a.berat_timbangan) for a in angkutan)
        total_berat_bersih = sum(float(a.berat_bersih) for a in angkutan)
        total_penjualan = sum(float(a.total_penjualan) for a in angkutan)
        rata_rata_harga = total_penjualan / total_berat_bersih if total_berat_bersih > 0 else 0
        
        return {
            'tahun': year,
            'bulan': month,
            'total_angkutan': angkutan.count(),
            'total_tandan': total_tandan,
            'total_berat_kotor': total_berat_kotor,
            'total_berat_bersih': total_berat_bersih,
            'total_potongan': total_berat_kotor - total_berat_bersih,
            'rata_rata_harga_per_kg': round(rata_rata_harga, 2),
            'total_penjualan': total_penjualan,
            'rata_rata_per_angkutan': round(total_penjualan / angkutan.count(), 2) if angkutan.count() > 0 else 0
        }

    def get_kelompok_penyetor(self):
        """Get the contributor group related to this transport"""
        kelompok_penyetor = self.kelompokpenyetor_set.all().values_list('nama_kelompok', flat=True)
        if kelompok_penyetor.exists():
            return " dan ".join(kelompok_penyetor)
        return ""


class KelompokPenyetor(models.Model):
    angkutan = models.ForeignKey(Angkutan, on_delete=models.CASCADE, blank=True, null=True)
    nama_kelompok = models.CharField(max_length=200, db_index=True, help_text="Nama Kelompok Tani")
    anggota_petani = models.ManyToManyField('petani.Petani', help_text="Petarni yang menyetor")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Kelompok Penyetor"
        verbose_name_plural = "Kelompok Penyetor"
        ordering = ['-updated_at']


class Lampiran(ThumbnailsMixin, models.Model):
    angkutan = models.OneToOneField(
        Angkutan,
        on_delete=models.CASCADE,
        related_name='lampiran_penjualan'
    )
    file_1 = models.FileField(
        upload_to='penjualan/file_1/',
        null=True,
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_1 = models.ImageField(upload_to='thumbs/penjualan/file_1/', null=True, blank=True)
    file_2 = models.FileField(
        upload_to='penjualan/file_2/',
        null=True,
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_2 = models.ImageField(upload_to='thumbs/penjualan/file_2/', null=True, blank=True)
    file_3 = models.FileField(
        upload_to='penjualan/file_3/',
        null=True,
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_3 = models.ImageField(upload_to='thumbs/penjualan/file_3/', null=True, blank=True)
    file_4 = models.FileField(
        upload_to='penjualan/file_4/',
        null=True,
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_4 = models.ImageField(upload_to='thumbs/penjualan/file_4/', null=True, blank=True)
    file_5 = models.FileField(
        upload_to='penjualan/file_5/',
        null=True,
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_5 = models.ImageField(upload_to='thumbs/penjualan/file_5/', null=True, blank=True)
    file_6 = models.FileField(
        upload_to='penjualan/file_6/',
        null=True,
        blank=True,
        validators=[MaxSizeFileValidator(10)]
    )
    thumb_6 = models.ImageField(upload_to='thumbs/penjualan/file_6/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lampiran Penjualan"
        verbose_name_plural = "Lampiran Penjualan"

    def __str__(self):
        return f"lampiran penjualan: {self.angkutan}"

    def _get_mapping_field_names(self):
        return {
            'file_1': 'thumb_1',
            'file_2': 'thumb_2',
            'file_3': 'thumb_3',
            'file_4': 'thumb_4',
            'file_5': 'thumb_5',
            'file_6': 'thumb_6',
        }

