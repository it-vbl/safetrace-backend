"""
Serializer Mixins for Signed Media URLs

Helper to auto-generate signed URLs in Django REST Framework serializers.

Usage:
    from utils.protected_medias.serializers import SignedMediaURLMixin
    
    class PekebunSerializer(SignedMediaURLMixin, serializers.ModelSerializer):
        # Fields that will be signed automatically
        signed_media_fields = ['foto_profile']
        
        class Meta:
            model = Pekebun
            fields = ['id', 'nama', 'foto_profile']
        
    # Output:
    {
        "id": 123,
        "nama": "Pak Budi",
        "foto_profile": "/media/profile_pictures/user123.jpg?expires=1234567890&signature=abc123..."
    }
"""
from django.conf import settings
from .signed_url import generate_signed_url, get_signed_url_from_field


class SignedMediaURLMixin:
    """
    Mixin for RESTFramework serializers that auto-generate signed URLs
    for FileField/ImageField.
    
    Attributes:
        signed_media_fields: List of field names that will be signed
        signed_media_expires_in: Expiration time (default: 3600 seconds / 1 hour)
    
    Example:
        class KebunSerializer(SignedMediaURLMixin, serializers.ModelSerializer):
            signed_media_fields = ['img_polygon', 'stdb_file']
            signed_media_expires_in = 7200  # 2 hours
            
            class Meta:
                model = Kebun
                fields = '__all__'
    """
    
    # Override in subclass
    signed_media_fields = []
    signed_media_expires_in = 3600  # 1 hour default
    
    def to_representation(self, instance):
        """Override to_representation to add signed URLs"""
        representation = super().to_representation(instance)
        
        # Check if feature is enabled in settings
        if not getattr(settings, 'ENABLE_SIGNED_MEDIA_URLS', True):
            return representation
        
        # Generate signed URLs for specified fields
        for field_name in self.signed_media_fields:
            if field_name in representation and representation[field_name]:
                # Get field from instance
                file_field = getattr(instance, field_name, None)
                
                if file_field:
                    signed_url = get_signed_url_from_field(
                        file_field, 
                        expires_in=self.signed_media_expires_in
                    )
                    
                    if signed_url:
                        representation[field_name] = signed_url
        
        return representation


def add_signed_urls_to_queryset_response(data, media_fields, expires_in=3600):
    """
    Helper function to add signed URLs to queryset response (list view).
    
    Useful for views that don't use serializers or custom response handling.
    
    Args:
        data: List of dict or single dict response
        media_fields: List of field names that contain media URLs
        expires_in: Expiration time in seconds
    
    Returns:
        Modified data with signed URLs
        
    Example:
        queryset = Pekebun.objects.all()
        data = list(queryset.values('id', 'nama', 'foto_profile'))
        data = add_signed_urls_to_queryset_response(
            data, 
            media_fields=['foto_profile'],
            expires_in=3600
        )
    """
    def process_item(item):
        for field_name in media_fields:
            if field_name in item and item[field_name]:
                file_path = item[field_name]
                signed_url = generate_signed_url(file_path, expires_in)
                if signed_url:
                    item[field_name] = signed_url
        return item
    
    if isinstance(data, list):
        return [process_item(item) for item in data]
    elif isinstance(data, dict):
        return process_item(data)
    else:
        return data


def get_signed_media_url(file_path_or_field, expires_in=3600):
    """
    Universal helper to generate signed URL from file path or FileField.
    
    Args:
        file_path_or_field: String path or FileField/ImageField instance
        expires_in: Expiration time in seconds
        
    Returns:
        String: Signed URL or None
        
    Example:
        # From string path
        signed_url = get_signed_media_url('profile_pictures/user123.jpg')
        
        # From FileField
        pekebun = Pekebun.objects.get(id=123)
        signed_url = get_signed_media_url(pekebun.foto_profile)
    """
    # Check if it's a FileField
    if hasattr(file_path_or_field, 'name'):
        return get_signed_url_from_field(file_path_or_field, expires_in)
    
    # It is a string path
    if isinstance(file_path_or_field, str):
        return generate_signed_url(file_path_or_field, expires_in)
    
    return None


class ConditionalSignedMediaMixin:
    """
    Mixin for serializers that conditionally generate signed URLs
    based on ENABLE_SIGNED_MEDIA_URLS setting.
    
    Backward compatible - if setting is False, return original URL.
    
    Usage:
        class PekebunSerializer(ConditionalSignedMediaMixin, serializers.ModelSerializer):
            foto_profile = serializers.SerializerMethodField()
            
            def get_foto_profile(self, obj):
                return self.get_media_url(obj.foto_profile, expires_in=3600)
            
            class Meta:
                model = Pekebun
                fields = ['id', 'nama', 'foto_profile']
    """
    
    def get_media_url(self, file_field, expires_in=3600):
        """
        Helper to generate URL (signed or original based on setting).
        
        Args:
            file_field: FileField/ImageField instance
            expires_in: Expiry time for signed URL (seconds)
            
        Returns:
            String: Signed URL or original URL or None
            
        Example:
            # In serializer method
            def get_foto_profile(self, obj):
                return self.get_media_url(obj.foto_profile, expires_in=3600)
        """
        if not file_field:
            return None
        
        # Check if signed URLs are enabled
        use_signed = getattr(settings, 'ENABLE_SIGNED_MEDIA_URLS', False)
        print(f"USE_SIGNED: {use_signed}, File: {file_field}")
        if use_signed:
            # Generate signed URL
            print("Generating signed URL for:", file_field)
            return get_signed_url_from_field(file_field, expires_in)
        
        # Fallback to original URL (existing behavior)
        try:
            media_host = getattr(settings, 'MEDIA_HOST', '')
            return f"{media_host}{file_field.url}"
        except (ValueError, AttributeError):
            # File does not exist
            return None
