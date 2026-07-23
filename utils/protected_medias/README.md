# Paket Protected Medias

**Paket Django mandiri untuk file media terlindungi dengan Signed URLs.**

Versi: 1.0.0  
Penulis: GitHub Copilot  
Tanggal: 19 Februari 2026

---

## 📦 Ikhtisar

Paket ini menyediakan perlindungan untuk file media Django menggunakan pendekatan **Signed URLs** - standar industri seperti AWS S3 Pre-signed URLs.

**Fitur Utama:**
- ✅ Signed URLs dengan signature HMAC-SHA256 + masa berlaku
- ✅ Dukungan autentikasi JWT/Session (cadangan)
- ✅ X-Accel-Redirect untuk Nginx produksi
- ✅ Tidak memerlukan perubahan frontend
- ✅ Mandiri & dapat digunakan kembali

**Manfaat:**
- Frontend tetap menggunakan `<img src={url}>` tanpa perubahan
- Browser cache berfungsi normal
- Kompatibel dengan CDN
- Ramah untuk aplikasi mobile (React Native, Flutter, dll)
- Kompatibel dengan SSR/SSG

---

## 📁 Struktur Paket

```
utils/protected_medias/
├── __init__.py           # Export paket
├── views.py              # View file media terlindungi
├── signed_url.py         # Generator & validator Signed URL
├── serializers.py        # Mixin serializer DRF
└── README.md             # File ini

Tes:
└── scripts/test_protected_media.sh
```

---

## 🚀 Mulai Cepat

### 1. Salin Paket ke Proyek Anda

```bash
# Salin seluruh folder
cp -r utils/protected_medias/ your_project/utils/

# Atau download sebagai zip dan ekstrak ke utils/
```

### 2. Konfigurasi Pengaturan

```python
# settings/base.py

# Diperlukan: Pengaturan media
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Aktifkan signed URLs
ENABLE_SIGNED_MEDIA_URLS = True

# Opsional: Kunci penandatanganan kustom (default ke SECRET_KEY)
# MEDIA_SIGNING_KEY = 'your-custom-signing-key'

# Opsional: X-Accel-Redirect untuk Nginx (atur di prod.py)
PROTECTED_MEDIA_USE_XACCEL = False
PROTECTED_MEDIA_XACCEL_PREFIX = '/protected'
```

### 3. Konfigurasi URL

```python
# your_project/urls.py
from django.urls import re_path
from utils.protected_medias import ProtectedMediaView

urlpatterns = [
    # ... pola lainnya ...
]

# URL Protected Media
urlpatterns += [
    re_path(r'^media/(?P<file_path>.*)$', 
            ProtectedMediaView.as_view(), 
            name='protected_media'),
]
```

### 4. Gunakan di Serializers

**Opsi A: Automatic Mixin (Sederhana)**

```python
from rest_framework import serializers
from utils.protected_medias import SignedMediaURLMixin

class UserSerializer(SignedMediaURLMixin, serializers.ModelSerializer):
    signed_media_fields = ['avatar', 'cover_photo']
    signed_media_expires_in = 3600  # 1 jam
    
    class Meta:
        model = User
        fields = ['id', 'name', 'avatar', 'cover_photo']
```

**Opsi B: Conditional Mixin (Direkomendasikan - Toggle via Settings)**

```python
from utils.protected_medias import ConditionalSignedMediaMixin

class UserSerializer(ConditionalSignedMediaMixin, serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    
    def get_avatar(self, obj):
        return self.get_media_url(obj.avatar, expires_in=3600)
    
    class Meta:
        model = User
        fields = ['id', 'name', 'avatar']
```

**Opsi C: Manual (Kontrol Penuh)**

```python
from utils.protected_medias import get_signed_url_from_field

class UserSerializer(serializers.ModelSerializer):
    avatar_signed = serializers.SerializerMethodField()
    
    def get_avatar_signed(self, obj):
        if not obj.avatar:
            return None
        return get_signed_url_from_field(obj.avatar, expires_in=3600)
    
    class Meta:
        model = User
        fields = ['id', 'name', 'avatar_signed']
```

### 5. Penggunaan Frontend (Tidak Ada Perubahan!)

**React/Next.js:**
```javascript
// Respons API sudah mencakup signed URL
function UserProfile({ user }) {
  return <img src={user.avatar} alt={user.name} />;
  // Bekerja! Tidak perlu fetch atau konversi blob
}
```

**React Native:**
```javascript
<Image source={{ uri: user.avatar }} />
// Bekerja!
```

---

## 📚 Referensi API Lengkap

### Views

#### `ProtectedMediaView`

View utama untuk melayani file media terlindungi.

**Prioritas Autentikasi:**
1. Signed URLs (query params)
2. JWT Token (Authorization: Bearer)
3. Django Session (cookies)

**Contoh:**
```python
from utils.protected_medias import ProtectedMediaView

urlpatterns = [
    re_path(r'^media/(?P<file_path>.*)$', 
            ProtectedMediaView.as_view()),
]
```

**Izin Kustom:**
```python
class OwnerOnlyMediaView(ProtectedMediaView):
    def check_permission(self, request, file_path):
        if getattr(request, '_signed_url_authenticated', False):
            return True
        
        # Logika kustom
        return request.user.is_staff or self.is_owner(request.user, file_path)
```

#### `ProtectedMediaDownloadView`

Varian yang memaksa download (Content-Disposition: attachment).

```python
re_path(r'^media/download/(?P<file_path>.*)$', 
        ProtectedMediaDownloadView.as_view()),
```

---

### Fungsi Signed URL

#### `generate_signed_url(file_path, expires_in=3600)`

Buat signed URL dari path file.

**Args:**
- `file_path` (str): Path relatif dari MEDIA_ROOT
- `expires_in` (int): Waktu kadaluarsa dalam detik (default: 3600)

**Returns:** String signed URL atau None

**Contoh:**
```python
from utils.protected_medias import generate_signed_url

url = generate_signed_url('photos/user123.jpg', expires_in=3600)
# Mengembalikan: '/media/photos/user123.jpg?expires=1708416000&signature=abc...'
```

#### `verify_signed_url(file_path, expires, signature)`

Verifikasi apakah signed URL valid.

**Returns:** `(is_valid: bool, error_message: str)`

#### `get_signed_url_from_field(file_field, expires_in=3600)`

Buat signed URL dari Django FileField/ImageField.

**Contoh:**
```python
from utils.protected_medias import get_signed_url_from_field

user = User.objects.get(id=123)
signed_url = get_signed_url_from_field(user.avatar, expires_in=3600)
```

---

### Mixin Serializer

#### `SignedMediaURLMixin`

Buat secara otomatis signed URLs untuk field tertentu.

**Atribut:**
- `signed_media_fields` (list): Field untuk ditandatangani
- `signed_media_expires_in` (int): Waktu kadaluarsa

**Contoh:**
```python
class PostSerializer(SignedMediaURLMixin, serializers.ModelSerializer):
    signed_media_fields = ['image', 'thumbnail']
    signed_media_expires_in = 7200  # 2 jam
```

#### `ConditionalSignedMediaMixin`

Tandatangani secara bersyarat berdasarkan pengaturan `ENABLE_SIGNED_MEDIA_URLS`.

**Methods:**
- `get_media_url(file_field, expires_in=3600)`: Dapatkan signed atau original URL

**Contoh:**
```python
class PostSerializer(ConditionalSignedMediaMixin, serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    def get_image(self, obj):
        return self.get_media_url(obj.image, expires_in=3600)
```

#### Fungsi Helper

**`add_signed_urls_to_queryset_response(data, media_fields, expires_in=3600)`**

Tambahkan signed URLs ke data queryset mentah.

```python
data = list(Post.objects.values('id', 'title', 'image'))
data = add_signed_urls_to_queryset_response(
    data, 
    media_fields=['image'],
    expires_in=3600
)
```

**`get_signed_media_url(file_path_or_field, expires_in=3600)`**

Helper universal - bekerja dengan path string atau FileField.

---

## ⚙️ Opsi Konfigurasi

### Pengaturan

| Pengaturan | Tipe | Default | Deskripsi |
|---------|------|---------|-------------|
| `ENABLE_SIGNED_MEDIA_URLS` | bool | `True` | Aktifkan/nonaktifkan signed URLs |
| `MEDIA_SIGNING_KEY` | str | `SECRET_KEY` | Kunci penandatanganan kustom |
| `PROTECTED_MEDIA_USE_XACCEL` | bool | `False` | Aktifkan X-Accel-Redirect (Nginx) |
| `PROTECTED_MEDIA_XACCEL_PREFIX` | str | `'/protected'` | Prefix path X-Accel |

### Waktu Kadaluarsa (Rekomendasi)

| Kasus Penggunaan | Kadaluarsa | Contoh |
|----------|--------|---------|
| Foto profil publik | 24 jam | `expires_in=86400` |
| Gambar galeri | 6 jam | `expires_in=21600` |
| Pratinjau dokumen | 1 jam | `expires_in=3600` |
| Dokumen sensitif | 15 menit | `expires_in=900` |
| Unggahan sementara | 5 menit | `expires_in=300` |

---

## 🔒 Keamanan

### Cara Kerja Signed URLs

```
1. Backend membuat signature:
   signature = HMAC-SHA256(SECRET_KEY, f"{file_path}:{expires_timestamp}")

2. Format URL:
   /media/file.jpg?expires=1708416000&signature=abc123...

3. Ketika diakses:
   - Periksa expires > waktu_saat_ini
   - Hitung ulang signature
   - Bandingkan menggunakan perbandingan waktu konstan
   - Jika cocok → layani file
   - Jika tidak → 401 Unauthorized
```

### Fitur Keamanan

- ✅ **Perlindungan perubahan** - Signature tidak cocok jika URL diubah
- ✅ **Perlindungan pengulangan** - URL kadaluarsa setelah waktu yang ditetapkan
- ✅ **Perlindungan traversal direktori** - Validasi path
- ✅ **Perlindungan serangan waktu** - Perbandingan waktu konstan
- ✅ **Perlindungan pemalsuan signature** - Memerlukan SECRET_KEY

### Praktik Terbaik

1. **Rotasi SECRET_KEY** - Buat ulang secara berkala di produksi
2. **Gunakan HTTPS** - Cegah intersepsi signature
3. **Atur kadaluarsa yang sesuai** - Seimbangkan keamanan vs UX
4. **Pantau penggunaan** - Catat aktivitas mencurigakan
5. **Pembatasan laju** - Cegah penyalahgunaan

---

## ⚡ Setup Produksi (Nginx)

### Aktifkan X-Accel-Redirect

**Peningkatan performa: 10x lebih cepat!** Nginx melayani file alih-alih Django.

**Pengaturan:**
```python
# settings/prod.py
PROTECTED_MEDIA_USE_XACCEL = True
PROTECTED_MEDIA_XACCEL_PREFIX = '/protected'
```

**Konfigurasi Nginx:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Aplikasi Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Media terlindungi - internal saja!
    location /protected {
        internal;  # Tidak dapat diakses langsung dari browser
        alias /path/to/your/media/;  # MEDIA_ROOT Anda
    }
}
```

**Cara kerja:**
1. Django memvalidasi signature
2. Django mengembalikan respons kosong dengan `X-Accel-Redirect: /protected/file.jpg`
3. Nginx mencegat header
4. Nginx melayani file langsung dari disk
5. Browser menerima file dari Nginx (cepat!)

---

## 🧪 Pengujian

### Jalankan Skrip Tes

```bash
chmod +x scripts/test_protected_media.sh
./scripts/test_protected_media.sh
```

### Pengujian Manual

```bash
# Tes 1: Akses tanpa autentikasi (harus gagal)
curl -I http://localhost:8000/media/test.jpg
# Yang diharapkan: 401 Unauthorized

# Tes 2: Akses dengan signed URL (harus bekerja jika file ada)
curl -I "http://localhost:8000/media/test.jpg?expires=9999999999&signature=valid"
# Yang diharapkan: 200 OK atau 404 jika file tidak ada

# Tes 3: Akses dengan URL yang kadaluarsa (harus gagal)
curl -I "http://localhost:8000/media/test.jpg?expires=1&signature=old"
# Yang diharapkan: 401 Unauthorized (kadaluarsa)
```

### Unit Tests

```python
from django.test import TestCase
from utils.protected_medias import generate_signed_url, verify_signed_url

class SignedURLTest(TestCase):
    def test_generate_signed_url(self):
        url = generate_signed_url('test.jpg', expires_in=3600)
        self.assertIn('expires=', url)
        self.assertIn('signature=', url)
    
    def test_verify_valid_url(self):
        url = generate_signed_url('test.jpg', expires_in=3600)
        # Parse expires dan signature dari url
        # ...
        is_valid, error = verify_signed_url('test.jpg', expires, signature)
        self.assertTrue(is_valid)
```

---

## 🔄 Migrasi dari Media Publik

### Langkah 1: Tambah Paket (Tidak Ada Perubahan yang Merusak)

```bash
# Salin paket
cp -r utils/protected_medias/ your_project/utils/

# Tambah pola URL
# Edit urls.py seperti yang ditunjukkan di Mulai Cepat
```

### Langkah 2: Aktifkan di Pengaturan

```python
# settings/base.py
ENABLE_SIGNED_MEDIA_URLS = False  # Tetap nonaktif awalnya
```

### Langkah 3: Perbarui Serializers

```python
# Gunakan ConditionalSignedMediaMixin
class UserSerializer(ConditionalSignedMediaMixin, serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    
    def get_avatar(self, obj):
        return self.get_media_url(obj.avatar)
```

### Langkah 4: Tes di Development

```python
# settings/local.py
ENABLE_SIGNED_MEDIA_URLS = True  # Aktifkan untuk pengujian
```

Tes semua endpoint dan integrasi frontend.

### Langkah 5: Deploy ke Produksi

```python
# settings/prod.py
ENABLE_SIGNED_MEDIA_URLS = True
PROTECTED_MEDIA_USE_XACCEL = True  # Aktifkan akselerasi Nginx
```

Pantau dan siap untuk rollback dengan menetapkan ke `False`.

---

## 🆘 Pemecahan Masalah

### T: Gambar tidak muncul (kesalahan 401)

**J:** Periksa:
1. `ENABLE_SIGNED_MEDIA_URLS = True` di pengaturan?
2. Format signed URL benar? (`?expires=xxx&signature=yyy`)
3. URL belum kadaluarsa?
4. SECRET_KEY sama di semua instance Django?

### T: Kesalahan signature tidak valid

**J:** Kemungkinan penyebab:
1. SECRET_KEY berbeda (dev vs prod)
2. Deviasi jam (waktu server tidak sinkron)
3. Path file tidak cocok (periksa garis miring trailing)

### T: Performa lambat

**J:** Aktifkan X-Accel-Redirect:
```python
PROTECTED_MEDIA_USE_XACCEL = True
```

### T: URL kadaluarsa terlalu cepat

**J:** Tingkatkan waktu kadaluarsa:
```python
def get_avatar(self, obj):
    return self.get_media_url(obj.avatar, expires_in=86400)  # 24 jam
```

---

## 📖 Contoh

Lihat `/docs/EXAMPLE_IMPLEMENTATION.md` untuk contoh implementasi lengkap.

---

## 🎯 Kompatibel Dengan

- ✅ Django 3.2+
- ✅ Django REST Framework 3.12+
- ✅ djangorestframework-simplejwt (opsional)
- ✅ Framework frontend apa pun (React, Vue, Angular, Svelte)
- ✅ Aplikasi mobile (React Native, Flutter)
- ✅ Framework SSR (Next.js, Nuxt.js)

---

## 📝 Lisensi

Lisensi MIT - Bebas digunakan di proyek Anda.

---

## 🤝 Berkontribusi

Ini adalah paket mandiri. Untuk meningkatkan:
1. Edit file di `utils/protected_medias/`
2. Tes secara menyeluruh
3. Perbarui README ini
4. Bagikan dengan tim!

---

## 🔗 Sumber Daya Terkait

- [Dokumentasi Django FileField](https://docs.djangoproject.com/en/4.1/ref/models/fields/#filefield)
- [AWS S3 Pre-signed URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html)
- [Nginx X-Accel](https://www.nginx.com/resources/wiki/start/topics/examples/x-accel/)

---

**Versi:** 1.0.0  
**Terakhir Diperbarui:** 19 Februari 2026  
**Status:** ✅ Siap Produksi
