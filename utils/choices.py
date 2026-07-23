from django.db import models


class JenisKelamin(models.TextChoices):
    LAKI_LAKI = '1', 'Laki-laki'
    PEREMPUAN = '2', 'Perempuan'


class StatusPerkawinan(models.TextChoices):
    BELUM_KAWIN = '1', 'Belum Kawin'
    KAWIN = '2', 'Kawin'
    CERAI_HIDUP = '3', 'Cerai Hidup'
    CERAI_MATI = '4', 'Cerai Mati'


class RequestOTPVia(models.TextChoices):
    EMAIL = '1', 'Email'
    SMS = '2', 'SMS'
    WA = '3', 'Whatapps'


class UserRole(models.TextChoices):
    ADMIN = '1', 'Admin'
    KETUA_KELOMPOK_TANI = '3', 'Ketua Kelompok Tani'
    DISBUNAK_KALBAR = '4', 'Disbunak Kalbar'
    DISBUNAK_SEKADAU = '5', 'Disbunak Sekadau'
    MITRA_PABRIK = '6', 'Mitra Pabrik' 


class JenisLegalitas(models.TextChoices):
    """
    Noted: Existing value
    SP = 3
    SJB = 4
    SPT = 5
    convert to 
    SP = 7
    SJB = 8
    SPT = 9
    """
    SHM = '1', 'Sertifikat Hak Milik (SHM)'
    SKT = '2', 'Girik/SKT/SKGR/Hak Pengelolaan'
    TANAH_ULAYAT = '3', 'Tanah ulayat/adat'
    HUTAN_SOSIAL = '4', 'Lahan Kawasan Hutan Produksi/Sosial'
    HUTAN_KONSERVASI = '5', 'Lahan Kawasan Hutan Produksi/Konservasi'
    SP = '7', 'Surat Pernyataan (SP)'
    SJB = '8', 'Surat Jaminan Bank (SJB)'
    SPT = '9', 'Surat Pernyataan Tanah (SPT)'


class RegisteredVia(models.TextChoices):
    ANDROID = '1', 'Android'
    IOS = '2', 'iOS'
    WEB_ADMIN = '3', 'Web Admin'
    WEB_IMPORT = '4', 'Web Import'


class PendidikanTerakhir(models.TextChoices):
    TIDAK_BERSEKOLAH = '1', 'Tidak punya ijazah SD'
    SD = '2', 'SD/Sederajat'
    SMP = '3', 'SMP/Sederajat'
    SMA = '4', 'SMA/Sederajat'
    D1 = '5', 'SMK'
    D2 = '6', 'D1/D2'
    D3 = '7', 'D3/Sarjana muda'
    S1 = '8', 'D4/S1'
    S2 = '9', 'S2/S3'
    LAINNYA = '99', 'Lainnya'


class SumberKontak(models.TextChoices):
    MANUAL = '1', 'Manual'
    UPLOAD_CSV = '2', 'Upload CSV'
    API = '3', 'API'


class StatusKeanggotaan(models.TextChoices):
    AKTIF = '1', 'Aktif'
    TIDAK_AKTIF = '0', 'Tidak Aktif'
    BELUM_ANGGOTA = '2', 'Belum Anggota'


class PenerimaBoardcast(models.TextChoices):
    INDIVIDU = '1', 'Kontak Individu'
    GRUP = '2', 'Kontak Grup'


class StatusPekerja(models.TextChoices):
    PEMILIK = '1', 'Pemilik'
    KELUARGA = '2', 'Keluarga'
    BURUH_TETAP = '3', 'Buruh Tetap'
    BURUH_HARIAN_TETAP = '4', 'Buruh Harian Lepas'
    

class WHISPStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    ERROR = 'error', 'Error'
    

class PilihanBulan(models.IntegerChoices):
    JANUARI = 1, 'Januari'
    FEBRUARI = 2, 'Februari'
    MARET = 3, 'Maret'
    APRIL = 4, 'April'
    MEI = 5, 'Mei'
    JUNI = 6, 'Juni'
    JULI = 7, 'Juli'
    AGUSTUS = 8, 'Agustus'
    SEPTEMBER = 9, 'September'
    OKTOBER = 10, 'Oktober'
    NOVEMBER = 11, 'November'
    DESEMBER = 12, 'Desember'


class DeforestationSourceType(models.TextChoices):
    GLAD = 'glad', 'GLAD'
    RADD = 'radd', 'RADD'


class StatusLahan(models.TextChoices):
    SHM = '1', 'Sertifikat Hak Milik'
    GIRIK_SKT = '2', 'Girik/SKT/SKGR/Hak Pengelolaan'
    TANAH_ADAT = '3', 'Tanah ulayat/adat'
    HUTAN_SOSIAL = '4', 'Lahan Kawasan Hutan Produksi/Sosial'
    HUTAN_KONSERVASI = '5', 'Lahan Kawasan Hutan Produksi/Konservasi'
    LAINNYA = '99', 'Lainnya (sebutkan)'
    

class PolaTanam(models.TextChoices):
    MONOKULTUR = '1', 'Monokultur'
    POLIKULTUR = '2', 'Polikultur'
    

class AsalBenih(models.TextChoices):
    BERSERTIFIKAT = '1', 'Produsen Benih Bersertifikat'
    TDK_BERSERTIFIKAT = '2', 'Produsen Benih Tidak Bersertifikat'
    TIDAK_TAHU = '3', 'Tidak Tahu'


class JenisLahan(models.TextChoices):
    LAHAN_MINERAL = '1', 'Lahan Mineral'
    LAHAN_BASAH = '2', 'Lahan Basa (Pasang Surut, Gambut)'


class JenisPupuk(models.TextChoices):
    ORGANIK = '1', 'Organik'
    ANORGANIK = '2', 'Anorganik'
    KOMBINASI = '3', 'Kombinasi'


class JenisPekerjaan(models.TextChoices):
    PANEN = '1', 'Panen'
    PUPUK = '2', 'Pupuk'
    SEMPROT = '3', 'Semprot'
    TEBAS = '4', 'Tebas'
    SUPIR = '5', 'Supir'
    LANGSIR = '6', 'Langsir'


class JenisAPD(models.TextChoices):
    APRON = '1', 'Apron'
    KACA_MATA = '2', 'Kaca Mata'
    SEPATU = '3', 'Sepatu'
    HELEM = '4', 'Helem'
    MASKER = '5', 'Masker'
    SARUNG_TANGAN = '6', 'Sarung Tangan'
    SARUNG_EGREK_DODOS = '7', 'Sarung egrek/dodos'


class KomoditasKelembagaan(models.TextChoices):
    CENGKEH = '14', 'CENGKEH'
    COKLAT_KAKAO = '15', 'COKLAT/KAKAO'
    KARET = '41', 'KARET'
    KELAPA = '52', 'KELAPA'
    KELAPA_SAWIT = '53', 'KELAPA SAWIT'
    KOPI = '69', 'KOPI'
    TEBU = '121', 'TEBU'
    TEH = '122', 'TEH'
    TEMBAKAU = '124', 'TEMBAKAU'
    PALA = '86', 'PALA'
    SEMUA = '0', 'SEMUA'
    LAINNYA = '99', 'LAINNYA'


class StatusSTDB(models.TextChoices):
    SUDAH_TERBIT = 'sudah_terbit', 'Sudah Terbit'
    BELUM_TERBIT = 'belum_terbit', 'Belum Terbit'
    DALAM_PROSES = 'dalam_proses', 'Dalam Proses'
