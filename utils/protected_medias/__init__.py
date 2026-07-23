"""
Protected Medias Package

Self-contained Django package untuk protected media files dengan signed URLs.

Quick Start:
    # 1. Add URL pattern
    from utils.protected_medias import ProtectedMediaView
    
    urlpatterns += [
        re_path(r'^media/(?P<file_path>.*)$', 
                ProtectedMediaView.as_view(), 
                name='protected_media'),
    ]
    
    # 2. Use in serializer
    from utils.protected_medias import ConditionalSignedMediaMixin
    
    class MySerializer(ConditionalSignedMediaMixin, serializers.ModelSerializer):
        foto = serializers.SerializerMethodField()
        
        def get_foto(self, obj):
            return self.get_media_url(obj.foto, expires_in=3600)
    
    # 3. Settings
    ENABLE_SIGNED_MEDIA_URLS = True

Features:
    - Signed URLs dengan HMAC-SHA256
    - JWT/Session authentication support
    - X-Accel-Redirect untuk Nginx
    - Zero frontend changes required

Documentation:
    See README.md in this directory for complete documentation.
"""

# Version
__version__ = '1.0.0'

# Main exports
from .views import ProtectedMediaView, ProtectedMediaDownloadView
from .signed_url import (
    generate_signed_url,
    verify_signed_url,
    get_signed_url_from_field,
)
from .serializers import (
    SignedMediaURLMixin,
    ConditionalSignedMediaMixin,
    add_signed_urls_to_queryset_response,
    get_signed_media_url,
)

__all__ = [
    # Views
    'ProtectedMediaView',
    'ProtectedMediaDownloadView',
    
    # Signed URL functions
    'generate_signed_url',
    'verify_signed_url',
    'get_signed_url_from_field',
    
    # Serializer mixins
    'SignedMediaURLMixin',
    'ConditionalSignedMediaMixin',
    'add_signed_urls_to_queryset_response',
    'get_signed_media_url',
]
