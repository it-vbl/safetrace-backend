from django.db import models
from utils.choices import PilihanBulan
from datetime import datetime


class Produksi(models.Model):
    kebun = models.ForeignKey('kebun.Kebun', on_delete=models.CASCADE)
    tahun = models.IntegerField(default=0, db_index=True)
    januari = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    februari = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    maret = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    april = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    mei = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    juni = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    juli = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    agustus = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    september = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    oktober = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    november = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    desember = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.tahun} - {self.kebun.petani}"

    def get_total_produksi(self):
        return (self.januari + self.februari + self.maret + self.april + 
               self.mei + self.juni + self.juli + self.agustus + 
               self.september + self.oktober + self.november + self.desember)

    def get_umur_tanaman(self):
        if self.tahun:
            current_year = datetime.now().year
            return current_year - self.tahun
        return 0

    def get_prod_ha_year(self):
        luas = self.kebun.luas_area_geom if self.kebun else 0
        produksi = self.get_total_produksi()
        return round(produksi / luas, 3) if luas > 0 else 0


class LB3(models.Model):
    kebun = models.ForeignKey('kebun.Kebun', on_delete=models.CASCADE)
    tahun = models.IntegerField(default=0, db_index=True)
    limbah_bobot = models.IntegerField(default=0, help_text='Satuan dalam kilogram (Kg)')
    limbah_jeriken = models.IntegerField(default=0, help_text='Satuan dalam kilogram (Kg)')
    limbah_karung_pupuk = models.IntegerField(default=0, help_text='Satuan dalam kilogram (Kg)')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.tahun} - {self.kebun.petani}"
    
    @property
    def umur_tanaman(self):
        """Crop age based on year"""
        current_year = datetime.now().year
        return current_year - self.tahun

    @property
    def total_lb3(self):
        return self.limbah_bobot + self.limbah_jeriken + self.limbah_karung_pupuk


class Pupuk(models.Model):
    kebun = models.ForeignKey('kebun.Kebun', on_delete=models.CASCADE)
    tahun = models.IntegerField(default=0, db_index=True)
    semester = models.IntegerField(choices=[(1, 'Semester 1'), (2, 'Semester 2')], help_text='Pilih semester')
    npk_jumlah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    natrium_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices, help_text='Pilih bulan', verbose_name='Natrium Waktu Aplikasi')
    natrium_jumlah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    postat_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices, help_text='Pilih bulan', verbose_name='Postat Waktu Aplikasi')
    postat_jumlah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    kalium_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices, help_text='Pilih bulan', verbose_name='Kalium Waktu Aplikasi')
    kalium_jumlah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    boron_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices, help_text='Pilih bulan', verbose_name='Boron Waktu Aplikasi')
    boron_jumlah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    magnesium_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices, help_text='Pilih bulan', verbose_name='Magnesium Waktu Aplikasi')
    magnesium_jumlah = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Satuan dalam kilogram (Kg)')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.tahun} - {self.kebun.petani}"


class PenggunaanPestisida(models.Model):
    """
    Model for storing yearly pesticide usage data.
    Covers semester 1 and semester 2 in a single record.
    """
    kebun = models.ForeignKey(
        'kebun.Kebun', 
        on_delete=models.CASCADE,
        related_name='penggunaan_pestisida'
    )
    tahun = models.IntegerField(db_index=True, help_text='Tahun aplikasi pestisida')
    
    # Semester 1 - Sistemik
    s1_sistemik_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pestisida sistemik semester 1',
        verbose_name='S1 Sistemik Waktu Aplikasi'
    )
    s1_sistemik_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pestisida sistemik dalam Liter',
        verbose_name='S1 Sistemik Jumlah'
    )
    
    # Semester 1 - Kontak
    s1_kontak_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pestisida kontak semester 1',
        verbose_name='S1 Kontak Waktu Aplikasi'
    )
    
    s1_kontak_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pestisida kontak dalam Liter',
        verbose_name='S1 Kontak Jumlah'
    )
    
    # Semester 2 - Sistemik
    s2_sistemik_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pestisida sistemik semester 2',
        verbose_name='S2 Sistemik Waktu Aplikasi'
    )
    s2_sistemik_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pestisida sistemik dalam Liter',
        verbose_name='S2 Sistemik Jumlah'
    )
    
    # Semester 2 - Kontak
    s2_kontak_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pestisida kontak semester 2',
        verbose_name='S2 Kontak Waktu Aplikasi'
    )
    s2_kontak_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pestisida kontak dalam Liter',
        verbose_name='S2 Kontak Jumlah'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Penggunaan Pestisida'
        verbose_name_plural = 'Penggunaan Pestisida'
        unique_together = [['kebun', 'tahun']]  # Satu record per kebun per tahun
        ordering = ['-tahun', 'kebun']
        indexes = [
            models.Index(fields=['kebun', 'tahun']),
        ]
    
    def __str__(self):
        return f"Pestisida {self.tahun} - {self.kebun.petani}"
    
    @property
    def total_sistemik(self):
        """Total systemic pesticide use (S1 + S2)"""
        return float(self.s1_sistemik_jumlah) + float(self.s2_sistemik_jumlah)
    
    @property
    def total_kontak(self):
        """Total contact pesticide use (S1 + S2)"""
        return float(self.s1_kontak_jumlah) + float(self.s2_kontak_jumlah)
    
    @property
    def total_pestisida(self):
        """Total all pesticide use"""
        return self.total_sistemik + self.total_kontak
    
    @property
    def intensitas_per_ha(self):
        """Pesticide use intensity per hectare"""
        if self.kebun and self.kebun.luas > 0:
            return round(self.total_pestisida / float(self.kebun.luas), 2)
        return 0
    
    @property
    def umur_tanaman(self):
        """Crop age based on year"""
        current_year = datetime.now().year
        return current_year - self.tahun
    
    def get_semester_data(self, semester):
        """Get data for a specific semester"""
        if semester == 1:
            return {
                'sistemik_waktu': self.get_s1_sistemik_waktu_aplikasi_display() if self.s1_sistemik_waktu_aplikasi else None,
                'sistemik_jumlah': float(self.s1_sistemik_jumlah),
                'kontak_waktu': self.get_s1_kontak_waktu_aplikasi_display() if self.s1_kontak_waktu_aplikasi else None,
                'kontak_jumlah': float(self.s1_kontak_jumlah),
            }
        elif semester == 2:
            return {
                'sistemik_waktu': self.get_s2_sistemik_waktu_aplikasi_display() if self.s2_sistemik_waktu_aplikasi else None,
                'sistemik_jumlah': float(self.s2_sistemik_jumlah),
                'kontak_waktu': self.get_s2_kontak_waktu_aplikasi_display() if self.s2_kontak_waktu_aplikasi else None,
                'kontak_jumlah': float(self.s2_kontak_jumlah),
            }
        return None
    
    
# gap/models.py

class PenggunaanPupuk(models.Model):
    """
    Model for storing yearly fertilizer usage data.
    Covers session 1, session 2, and session 3 in a single record.
    """
    kebun = models.ForeignKey(
        'kebun.Kebun', 
        on_delete=models.CASCADE,
        related_name='penggunaan_pupuk'
    )
    tahun = models.IntegerField(db_index=True, help_text='Tahun aplikasi pupuk')
    
    # ============ SESSION 1 ============
    
    # NPK - Session 1
    s1_npk_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk NPK sesi 1',
        verbose_name='S1 NPK Waktu Aplikasi'
    )
    s1_npk_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk NPK dalam Kg',
        verbose_name='S1 NPK Jumlah'
    )
    
    # Nitrogen - Session 1
    s1_nitrogen_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Nitrogen sesi 1',
        verbose_name='S1 Nitrogen Waktu Aplikasi'
    )
    s1_nitrogen_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Nitrogen dalam Kg',
        verbose_name='S1 Nitrogen Jumlah'
    )
    
    # Postpat - Session 1
    s1_postpat_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Postpat sesi 1',
        verbose_name='S1 Postpat Waktu Aplikasi'
    )
    s1_postpat_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Postpat dalam Kg',
        verbose_name='S1 Postpat Jumlah'
    )
    
    # Kalium - Session 1
    s1_kalium_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Kalium sesi 1',
        verbose_name='S1 Kalium Waktu Aplikasi'
    )
    s1_kalium_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Kalium dalam Kg',
        verbose_name='S1 Kalium Jumlah'
    )
    
    # Boron - Session 1
    s1_boron_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Boron sesi 1',
        verbose_name='S1 Boron Waktu Aplikasi'
    )
    s1_boron_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Boron dalam Kg',
        verbose_name='S1 Boron Jumlah'
    )
    
    # Magnesium - Session 1
    s1_magnesium_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Magnesium sesi 1',
        verbose_name='S1 Magnesium Waktu Aplikasi'
    )
    s1_magnesium_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Magnesium dalam Kg',
        verbose_name='S1 Magnesium Jumlah'
    )
    
    # ============ SESSION 2 ============
    
    # NPK - Session 2
    s2_npk_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk NPK sesi 2',
        verbose_name='S2 NPK Waktu Aplikasi'
    )
    s2_npk_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk NPK dalam Kg',
        verbose_name='S2 NPK Jumlah'
    )
    
    # Nitrogen - Session 2
    s2_nitrogen_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Nitrogen sesi 2',
        verbose_name='S2 Nitrogen Waktu Aplikasi'
    )
    s2_nitrogen_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Nitrogen dalam Kg',
        verbose_name='S2 Nitrogen Jumlah'
    )
    
    # Postpat - Session 2
    s2_postpat_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Postpat sesi 2',
        verbose_name='S2 Postpat Waktu Aplikasi'
    )
    s2_postpat_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Postpat dalam Kg',
        verbose_name='S2 Postpat Jumlah'
    )
    
    # Kalium - Session 2
    s2_kalium_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Kalium sesi 2',
        verbose_name='S2 Kalium Waktu Aplikasi'
    )
    s2_kalium_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Kalium dalam Kg',
        verbose_name='S2 Kalium Jumlah'
    )
    
    # Boron - Session 2
    s2_boron_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Boron sesi 2',
        verbose_name='S2 Boron Waktu Aplikasi'
    )
    s2_boron_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Boron dalam Kg',
        verbose_name='S2 Boron Jumlah'
    )
    
    # Magnesium - Session 2
    s2_magnesium_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Magnesium sesi 2',
        verbose_name='S2 Magnesium Waktu Aplikasi'
    )
    s2_magnesium_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Magnesium dalam Kg',
        verbose_name='S2 Magnesium Jumlah'
    )
    
    # ============ SESSION 3 ============
    
    # NPK - Session 3
    s3_npk_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk NPK sesi 3',
        verbose_name='S3 NPK Waktu Aplikasi'
    )
    s3_npk_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk NPK dalam Kg',
        verbose_name='S3 NPK Jumlah'
    )
    
    # Nitrogen - Session 3
    s3_nitrogen_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Nitrogen sesi 3',
        verbose_name='S3 Nitrogen Waktu Aplikasi'
    )
    s3_nitrogen_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Nitrogen dalam Kg',
        verbose_name='S3 Nitrogen Jumlah'
    )
    
    # Postpat - Session 3
    s3_postpat_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Postpat sesi 3',
        verbose_name='S3 Postpat Waktu Aplikasi'
    )
    s3_postpat_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Postpat dalam Kg',
        verbose_name='S3 Postpat Jumlah'
    )
    
    # Kalium - Session 3
    s3_kalium_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Kalium sesi 3',
        verbose_name='S3 Kalium Waktu Aplikasi'
    )
    s3_kalium_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Kalium dalam Kg',
        verbose_name='S3 Kalium Jumlah'
    )
    
    # Boron - Session 3
    s3_boron_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Boron sesi 3',
        verbose_name='S3 Boron Waktu Aplikasi'
    )
    s3_boron_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Boron dalam Kg',
        verbose_name='S3 Boron Jumlah'
    )
    
    # Magnesium - Session 3
    s3_magnesium_waktu_aplikasi = models.IntegerField(
        choices=PilihanBulan.choices,
        null=True,
        blank=True,
        help_text='Bulan aplikasi pupuk Magnesium sesi 3',
        verbose_name='S3 Magnesium Waktu Aplikasi'
    )
    s3_magnesium_jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Jumlah pupuk Magnesium dalam Kg',
        verbose_name='S3 Magnesium Jumlah'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Penggunaan Pupuk'
        verbose_name_plural = 'Penggunaan Pupuk'
        unique_together = [['kebun', 'tahun']]
        ordering = ['-tahun', 'kebun']
        indexes = [
            models.Index(fields=['kebun', 'tahun']),
        ]
    
    def __str__(self):
        return f"Pupuk {self.tahun} - {self.kebun.petani}"
    
    # ========== HELPER METHODS - SESSION 1 ==========
    
    @property
    def s1_total_npk(self):
        """Total NPK session 1"""
        return float(self.s1_npk_jumlah)
    
    @property
    def s1_total_nitrogen(self):
        """Total Nitrogen session 1"""
        return float(self.s1_nitrogen_jumlah)
    
    @property
    def s1_total_postpat(self):
        """Total Postpat session 1"""
        return float(self.s1_postpat_jumlah)
    
    @property
    def s1_total_kalium(self):
        """Total Kalium session 1"""
        return float(self.s1_kalium_jumlah)
    
    @property
    def s1_total_boron(self):
        """Total Boron session 1"""
        return float(self.s1_boron_jumlah)
    
    @property
    def s1_total_magnesium(self):
        """Total Magnesium session 1"""
        return float(self.s1_magnesium_jumlah)
    
    @property
    def s1_total_pupuk(self):
        """Total all fertilizers in session 1"""
        return (self.s1_total_npk + self.s1_total_nitrogen + 
                self.s1_total_postpat + self.s1_total_kalium + 
                self.s1_total_boron + self.s1_total_magnesium)
    
    # ========== HELPER METHODS - SESSION 2 ==========
    
    @property
    def s2_total_npk(self):
        """Total NPK session 2"""
        return float(self.s2_npk_jumlah)
    
    @property
    def s2_total_nitrogen(self):
        """Total Nitrogen session 2"""
        return float(self.s2_nitrogen_jumlah)
    
    @property
    def s2_total_postpat(self):
        """Total Postpat session 2"""
        return float(self.s2_postpat_jumlah)
    
    @property
    def s2_total_kalium(self):
        """Total Kalium session 2"""
        return float(self.s2_kalium_jumlah)
    
    @property
    def s2_total_boron(self):
        """Total Boron session 2"""
        return float(self.s2_boron_jumlah)
    
    @property
    def s2_total_magnesium(self):
        """Total Magnesium session 2"""
        return float(self.s2_magnesium_jumlah)
    
    @property
    def s2_total_pupuk(self):
        """Total all fertilizers in session 2"""
        return (self.s2_total_npk + self.s2_total_nitrogen + 
                self.s2_total_postpat + self.s2_total_kalium + 
                self.s2_total_boron + self.s2_total_magnesium)
    
    # ========== HELPER METHODS - SESSION 3 ==========
    
    @property
    def s3_total_npk(self):
        """Total NPK session 3"""
        return float(self.s3_npk_jumlah)
    
    @property
    def s3_total_nitrogen(self):
        """Total Nitrogen session 3"""
        return float(self.s3_nitrogen_jumlah)
    
    @property
    def s3_total_postpat(self):
        """Total Postpat session 3"""
        return float(self.s3_postpat_jumlah)
    
    @property
    def s3_total_kalium(self):
        """Total Kalium session 3"""
        return float(self.s3_kalium_jumlah)
    
    @property
    def s3_total_boron(self):
        """Total Boron session 3"""
        return float(self.s3_boron_jumlah)
    
    @property
    def s3_total_magnesium(self):
        """Total Magnesium session 3"""
        return float(self.s3_magnesium_jumlah)
    
    @property
    def s3_total_pupuk(self):
        """Total all fertilizers in session 3"""
        return (self.s3_total_npk + self.s3_total_nitrogen + 
                self.s3_total_postpat + self.s3_total_kalium + 
                self.s3_total_boron + self.s3_total_magnesium)
    
    # ========== HELPER METHODS - ANNUAL TOTAL ==========
    
    @property
    def total_npk(self):
        """Annual total NPK (S1 + S2 + S3)"""
        return self.s1_total_npk + self.s2_total_npk + self.s3_total_npk
    
    @property
    def total_nitrogen(self):
        """Annual total Nitrogen (S1 + S2 + S3)"""
        return self.s1_total_nitrogen + self.s2_total_nitrogen + self.s3_total_nitrogen
    
    @property
    def total_postpat(self):
        """Annual total Postpat (S1 + S2 + S3)"""
        return self.s1_total_postpat + self.s2_total_postpat + self.s3_total_postpat
    
    @property
    def total_kalium(self):
        """Annual total Kalium (S1 + S2 + S3)"""
        return self.s1_total_kalium + self.s2_total_kalium + self.s3_total_kalium
    
    @property
    def total_boron(self):
        """Annual total Boron (S1 + S2 + S3)"""
        return self.s1_total_boron + self.s2_total_boron + self.s3_total_boron
    
    @property
    def total_magnesium(self):
        """Annual total Magnesium (S1 + S2 + S3)"""
        return self.s1_total_magnesium + self.s2_total_magnesium + self.s3_total_magnesium
    
    @property
    def total_pupuk(self):
        """Annual total of all fertilizers"""
        return self.s1_total_pupuk + self.s2_total_pupuk + self.s3_total_pupuk
    
    @property
    def intensitas_per_ha(self):
        """Fertilizer usage intensity per hectare"""
        if self.kebun and self.kebun.luas > 0:
            return round(self.total_pupuk / float(self.kebun.luas), 2)
        return 0
    
    @property
    def umur_tanaman(self):
        """Crop age based on year"""
        current_year = datetime.now().year
        return current_year - self.tahun
    
    def get_semester_data(self, semester):
        """Get data for a specific session (1, 2, or 3)"""
        if semester == 1:
            return {
                'npk': {
                    'waktu': self.get_s1_npk_waktu_aplikasi_display() if self.s1_npk_waktu_aplikasi else None,
                    'jumlah': float(self.s1_npk_jumlah)
                },
                'nitrogen': {
                    'waktu': self.get_s1_nitrogen_waktu_aplikasi_display() if self.s1_nitrogen_waktu_aplikasi else None,
                    'jumlah': float(self.s1_nitrogen_jumlah)
                },
                'postpat': {
                    'waktu': self.get_s1_postpat_waktu_aplikasi_display() if self.s1_postpat_waktu_aplikasi else None,
                    'jumlah': float(self.s1_postpat_jumlah)
                },
                'kalium': {
                    'waktu': self.get_s1_kalium_waktu_aplikasi_display() if self.s1_kalium_waktu_aplikasi else None,
                    'jumlah': float(self.s1_kalium_jumlah)
                },
                'boron': {
                    'waktu': self.get_s1_boron_waktu_aplikasi_display() if self.s1_boron_waktu_aplikasi else None,
                    'jumlah': float(self.s1_boron_jumlah)
                },
                'magnesium': {
                    'waktu': self.get_s1_magnesium_waktu_aplikasi_display() if self.s1_magnesium_waktu_aplikasi else None,
                    'jumlah': float(self.s1_magnesium_jumlah)
                },
                'total': self.s1_total_pupuk
            }
        elif semester == 2:
            return {
                'npk': {
                    'waktu': self.get_s2_npk_waktu_aplikasi_display() if self.s2_npk_waktu_aplikasi else None,
                    'jumlah': float(self.s2_npk_jumlah)
                },
                'nitrogen': {
                    'waktu': self.get_s2_nitrogen_waktu_aplikasi_display() if self.s2_nitrogen_waktu_aplikasi else None,
                    'jumlah': float(self.s2_nitrogen_jumlah)
                },
                'postpat': {
                    'waktu': self.get_s2_postpat_waktu_aplikasi_display() if self.s2_postpat_waktu_aplikasi else None,
                    'jumlah': float(self.s2_postpat_jumlah)
                },
                'kalium': {
                    'waktu': self.get_s2_kalium_waktu_aplikasi_display() if self.s2_kalium_waktu_aplikasi else None,
                    'jumlah': float(self.s2_kalium_jumlah)
                },
                'boron': {
                    'waktu': self.get_s2_boron_waktu_aplikasi_display() if self.s2_boron_waktu_aplikasi else None,
                    'jumlah': float(self.s2_boron_jumlah)
                },
                'magnesium': {
                    'waktu': self.get_s2_magnesium_waktu_aplikasi_display() if self.s2_magnesium_waktu_aplikasi else None,
                    'jumlah': float(self.s2_magnesium_jumlah)
                },
                'total': self.s2_total_pupuk
            }
        elif semester == 3:
            return {
                'npk': {
                    'waktu': self.get_s3_npk_waktu_aplikasi_display() if self.s3_npk_waktu_aplikasi else None,
                    'jumlah': float(self.s3_npk_jumlah)
                },
                'nitrogen': {
                    'waktu': self.get_s3_nitrogen_waktu_aplikasi_display() if self.s3_nitrogen_waktu_aplikasi else None,
                    'jumlah': float(self.s3_nitrogen_jumlah)
                },
                'postpat': {
                    'waktu': self.get_s3_postpat_waktu_aplikasi_display() if self.s3_postpat_waktu_aplikasi else None,
                    'jumlah': float(self.s3_postpat_jumlah)
                },
                'kalium': {
                    'waktu': self.get_s3_kalium_waktu_aplikasi_display() if self.s3_kalium_waktu_aplikasi else None,
                    'jumlah': float(self.s3_kalium_jumlah)
                },
                'boron': {
                    'waktu': self.get_s3_boron_waktu_aplikasi_display() if self.s3_boron_waktu_aplikasi else None,
                    'jumlah': float(self.s3_boron_jumlah)
                },
                'magnesium': {
                    'waktu': self.get_s3_magnesium_waktu_aplikasi_display() if self.s3_magnesium_waktu_aplikasi else None,
                    'jumlah': float(self.s3_magnesium_jumlah)
                },
                'total': self.s3_total_pupuk
            }
        return None