# 📦 Protected Medias Package - Installation Guide

Complete self-contained package for securing Django media files with Signed URLs.

---

## 📂 What's Included

This package contains everything you need to implement protected media files:

```
utils/protected_medias/
├── __init__.py              # Package exports (v1.0.0)
├── views.py                 # ProtectedMediaView & ProtectedMediaDownloadView
├── signed_url.py            # Signed URL generation & validation
├── serializers.py           # DRF mixins (SignedMediaURLMixin, etc)
└── README.md                # Complete documentation (this file)

Supporting Files:
├── scripts/test_protected_media.sh    # Test script
└── docs/
    ├── EXAMPLE_IMPLEMENTATION.md      # Code examples
    ├── SIGNED_URLS_NEXTJS.md          # Next.js integration
    └── PROTECTED_MEDIA.md             # Technical reference
```

**Total Size:** ~100KB  
**Dependencies:** Django 3.2+, Django REST Framework (optional)

---

## 🚀 Quick Installation (3 Steps)

### Method 1: Copy Single Folder (Recommended)

```bash
# 1. Copy the package to your new project
cp -r utils/protected_medias/ /path/to/your_project/utils/

# 2. Add to settings
# 3. Add to URLs

# Done! 🎉
```

### Method 2: Download as Archive

```bash
# 1. Create package archive
cd /path/to/current_project
tar -czf protected_medias.tar.gz utils/protected_medias/

# 2. Transfer to new project
scp protected_medias.tar.gz user@server:/path/to/new_project/

# 3. Extract in new project
cd /path/to/new_project
tar -xzf protected_medias.tar.gz
```

---

## ⚙️ Configuration Steps

### Step 1: Settings Configuration

Add to your `settings/base.py`:

```python
# ============================================
# PROTECTED MEDIA SETTINGS
# ============================================

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'  # or os.path.join(BASE_DIR, 'media')

# Enable Signed URLs (toggle globally)
ENABLE_SIGNED_MEDIA_URLS = True

# Optional: Custom signing key (defaults to SECRET_KEY)
# Recommended for production to separate concerns
# MEDIA_SIGNING_KEY = 'your-custom-signing-key-here'

# Optional: X-Accel-Redirect for Nginx (set in prod.py)
PROTECTED_MEDIA_USE_XACCEL = False
PROTECTED_MEDIA_XACCEL_PREFIX = '/protected'
```

**Production settings** (`settings/prod.py`):

```python
# Enable X-Accel-Redirect for faster file serving (10x performance boost)
PROTECTED_MEDIA_USE_XACCEL = True
PROTECTED_MEDIA_XACCEL_PREFIX = '/protected'

# Optional: Use separate signing key
import os
MEDIA_SIGNING_KEY = os.environ.get('MEDIA_SIGNING_KEY', SECRET_KEY)
```

### Step 2: URL Configuration

Add to your main `urls.py`:

```python
from django.urls import path, re_path, include
from django.conf import settings
from utils.protected_medias import ProtectedMediaView

urlpatterns = [
    # Your existing patterns
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    # ...
]

# Protected Media URLs
# IMPORTANT: Add this BEFORE any catch-all patterns
urlpatterns += [
    re_path(r'^media/(?P<file_path>.*)$', 
            ProtectedMediaView.as_view(), 
            name='protected_media'),
]
```

**Optional:** Add download variant:

```python
from utils.protected_medias import ProtectedMediaDownloadView

urlpatterns += [
    re_path(r'^media/download/(?P<file_path>.*)$', 
            ProtectedMediaDownloadView.as_view(), 
            name='protected_media_download'),
]
```

### Step 3: Use in Serializers

Choose one of three approaches:

#### A. Automatic Mixin (Simplest)

```python
from rest_framework import serializers
from utils.protected_medias import SignedMediaURLMixin

class UserSerializer(SignedMediaURLMixin, serializers.ModelSerializer):
    # Specify which fields to auto-sign
    signed_media_fields = ['profile_photo', 'cover_image']
    signed_media_expires_in = 3600  # 1 hour
    
    class Meta:
        model = User
        fields = ['id', 'name', 'profile_photo', 'cover_image']
```

#### B. Conditional Mixin (Recommended - Production Safe)

```python
from utils.protected_medias import ConditionalSignedMediaMixin

class UserSerializer(ConditionalSignedMediaMixin, serializers.ModelSerializer):
    profile_photo = serializers.SerializerMethodField()
    
    def get_profile_photo(self, obj):
        # Returns signed URL if ENABLE_SIGNED_MEDIA_URLS=True
        # Returns original URL if False
        return self.get_media_url(obj.profile_photo, expires_in=3600)
    
    class Meta:
        model = User
        fields = ['id', 'name', 'profile_photo']
```

#### C. Manual (Full Control)

```python
from utils.protected_medias import get_signed_url_from_field

class UserSerializer(serializers.ModelSerializer):
    profile_photo_signed = serializers.SerializerMethodField()
    
    def get_profile_photo_signed(self, obj):
        if not obj.profile_photo:
            return None
        return get_signed_url_from_field(obj.profile_photo, expires_in=7200)
    
    class Meta:
        model = User
        fields = ['id', 'name', 'profile_photo_signed']
```

---

## 🧪 Testing

### Quick Test

```bash
# 1. Copy test script
cp scripts/test_protected_media.sh /path/to/new_project/scripts/

# 2. Make executable
chmod +x scripts/test_protected_media.sh

# 3. Run tests
./scripts/test_protected_media.sh
```

### Manual Test

```bash
# Start Django server
python manage.py runserver

# In another terminal:

# Test 1: Unauthenticated access (should fail 401)
curl -I http://localhost:8000/media/test.jpg

# Test 2: With signed URL (should work if file exists)
# Get signed URL from API endpoint first, then:
curl -I "http://localhost:8000/media/test.jpg?expires=9999999999&signature=xxx"
```

### Django Shell Test

```bash
python manage.py shell
```

```python
from utils.protected_medias import generate_signed_url, verify_signed_url

# Test URL generation
url = generate_signed_url('photos/test.jpg', expires_in=3600)
print(f"Signed URL: {url}")

# Test verification
import re
match = re.search(r'expires=(\d+)&signature=([^&]+)', url)
expires = match.group(1)
signature = match.group(2)

is_valid, error = verify_signed_url('photos/test.jpg', int(expires), signature)
print(f"Valid: {is_valid}")
```

---

## 🔧 Nginx Configuration (Production)

### Enable X-Accel-Redirect

**Settings:**
```python
# settings/prod.py
PROTECTED_MEDIA_USE_XACCEL = True
PROTECTED_MEDIA_XACCEL_PREFIX = '/protected'
```

**Nginx Config:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Django application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Protected media - internal only!
    location /protected {
        internal;  # Cannot be accessed directly from browser
        alias /path/to/your/media/;  # Your MEDIA_ROOT (absolute path)
    }
}
```

**Verify Nginx config:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔒 Security Checklist

Before going to production:

- [ ] Set `ENABLE_SIGNED_MEDIA_URLS = True` in production settings
- [ ] Use HTTPS (required for secure signature transmission)
- [ ] Set appropriate `expires_in` values (balance security vs UX)
- [ ] Consider separate `MEDIA_SIGNING_KEY` (not required but recommended)
- [ ] Enable `PROTECTED_MEDIA_USE_XACCEL = True` for Nginx
- [ ] Test with expired URLs (should return 401)
- [ ] Test with tampered signatures (should return 401)
- [ ] Verify no direct media access without signature
- [ ] Set up monitoring for 401 errors (potential abuse)

---

## 🚦 Migration Strategy (Zero Downtime)

If you're adding this to an existing project with public media:

### Phase 1: Install Package (No Breaking Changes)

```python
# settings.py
ENABLE_SIGNED_MEDIA_URLS = False  # Keep disabled
```

Install package and add URLs. No impact on existing frontend.

### Phase 2: Update Serializers

```python
# Use ConditionalSignedMediaMixin
class UserSerializer(ConditionalSignedMediaMixin, serializers.ModelSerializer):
    profile_photo = serializers.SerializerMethodField()
    
    def get_profile_photo(self, obj):
        return self.get_media_url(obj.profile_photo)
```

Deploy. Still no breaking changes (returns original URLs).

### Phase 3: Enable in Development

```python
# settings/local.py
ENABLE_SIGNED_MEDIA_URLS = True
```

Test thoroughly with frontend.

### Phase 4: Enable in Production

```python
# settings/prod.py
ENABLE_SIGNED_MEDIA_URLS = True
PROTECTED_MEDIA_USE_XACCEL = True
```

Deploy and monitor. Can rollback by changing setting to `False`.

---

## 📖 Full Documentation

Detailed guides available in `utils/protected_medias/README.md`:

- Complete API reference
- Security best practices
- Troubleshooting guide
- Production optimization
- Code examples

Additional docs (optional - can be copied if needed):
- `docs/EXAMPLE_IMPLEMENTATION.md` - Practical examples
- `docs/SIGNED_URLS_NEXTJS.md` - Next.js/React integration
- `docs/PROTECTED_MEDIA.md` - Technical deep dive

---

## 🆘 Troubleshooting

### Images not loading (401 error)

**Check:**
1. `ENABLE_SIGNED_MEDIA_URLS = True` in settings?
2. URLs have `?expires=xxx&signature=yyy` format?
3. URL not expired?
4. SECRET_KEY consistent across all Django instances?

**Debug:**
```python
from utils.protected_medias import generate_signed_url
url = generate_signed_url('test.jpg')
print(url)  # Should have expires and signature
```

### Signature always invalid

**Possible causes:**
1. Different SECRET_KEY between environments
2. Clock skew (server time not synchronized)
3. File path mismatch (check trailing slashes)

**Solution:**
```bash
# Sync server time
sudo ntpdate -s time.nist.gov

# Check SECRET_KEY
python manage.py shell -c "from django.conf import settings; print(settings.SECRET_KEY[:10])"
```

### Slow performance

**Solution:** Enable X-Accel-Redirect:
```python
PROTECTED_MEDIA_USE_XACCEL = True
```

Performance boost: ~10x faster file serving.

---

## 📦 Package Dependencies

**Required:**
- Django >= 3.2
- Python >= 3.8

**Optional:**
- djangorestframework >= 3.12 (for serializer mixins)
- djangorestframework-simplejwt (for JWT auth support)

**No external packages required!** Uses only Django built-ins:
- `hmac` (Python standard library)
- `hashlib` (Python standard library)
- `django.views` (Django built-in)
- `django.http` (Django built-in)

---

## ✅ Installation Checklist

Use this checklist when installing in a new project:

- [ ] Copy `utils/protected_medias/` folder
- [ ] Add settings configuration
- [ ] Add URL patterns
- [ ] Update serializers to use mixins
- [ ] Run `python manage.py check` (should pass)
- [ ] Test unauthenticated access (should 401)
- [ ] Test with signed URL (should work)
- [ ] Configure Nginx X-Accel-Redirect (production)
- [ ] Enable in production with monitoring
- [ ] Document for your team

---

## 🎯 Compatible Environments

**Backend:**
- ✅ Django 3.2, 4.0, 4.1, 4.2, 5.0
- ✅ Python 3.8, 3.9, 3.10, 3.11, 3.12
- ✅ Any WSGI server (Gunicorn, uWSGI, etc)
- ✅ Any reverse proxy (Nginx, Apache, Caddy)

**Frontend:**
- ✅ React / Next.js
- ✅ Vue / Nuxt.js
- ✅ Angular
- ✅ Svelte / SvelteKit
- ✅ React Native
- ✅ Flutter
- ✅ Any SSR/SSG framework

**Deployment:**
- ✅ Docker / Docker Compose
- ✅ Kubernetes
- ✅ Traditional VPS
- ✅ Cloud platforms (AWS, GCP, Azure, DigitalOcean)

---

## 📝 License

MIT License - Free to use in your projects.

---

## 💡 Quick Reference

**Generate signed URL in code:**
```python
from utils.protected_medias import get_signed_url_from_field
url = get_signed_url_from_field(user.avatar, expires_in=3600)
```

**Frontend usage (no changes needed):**
```jsx
<img src={user.avatar} alt="Profile" />
// Works! No fetch, no blob conversion
```

**Toggle feature:**
```python
# settings.py
ENABLE_SIGNED_MEDIA_URLS = True  # or False
```

**Performance boost (Nginx):**
```python
PROTECTED_MEDIA_USE_XACCEL = True
```

---

**Version:** 1.0.0  
**Status:** ✅ Production Ready  
**Last Updated:** February 19, 2026

For questions or issues, refer to `utils/protected_medias/README.md`
