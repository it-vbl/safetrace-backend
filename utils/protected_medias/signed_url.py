"""
Signed URL Generator for Protected Media Files

Generate temporary signed URLs for media files that can be used directly
in frontend without needing JWT token in Authorization header.

Benefits:
- Frontend doesn't need fetch + blob conversion
- Can be used directly in <img src={signedUrl}>
- URL secured with HMAC signature
- Auto-expires after certain time
- Cannot be forged without secret key

Usage Backend (API Response):
    from utils.signed_url import generate_signed_url
    
    # In serializer or view
    foto_url = generate_signed_url(user.photo_profile.name, expires_in=3600)
    return {
        'foto_profile': foto_url  # /media/...?expires=xxx&signature=yyy
    }

Usage Frontend (No change needed!):
    <img src={user.foto_profile} />  // Works! No fetch needed
"""
import hashlib
import hmac
import time
from urllib.parse import urlencode, urlparse, parse_qs
from django.conf import settings
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature


def get_signing_key():
    """
    Get secret key for signing URLs.
    Use dedicated key or fallback to SECRET_KEY.
    """
    return getattr(
        settings, 
        'MEDIA_SIGNING_KEY', 
        settings.SECRET_KEY
    )


def generate_signed_url(file_path, expires_in=3600):
    """
    Generate signed URL for media file.
    
    Args:
        file_path: Relative path from MEDIA_ROOT (e.g., 'profile_pictures/user123.jpg')
        expires_in: Expiration time in seconds (default: 3600 = 1 hour)
        
    Returns:
        String: Full URL with signature
        
    Example:
        >>> generate_signed_url('profile_pictures/user123.jpg', expires_in=3600)
        '/media/profile_pictures/user123.jpg?expires=1234567890&signature=abc123...'
    """
    if not file_path:
        return None
    
    # Remove leading slash if present
    file_path = file_path.lstrip('/')
    
    # Remove /media/ prefix if present
    if file_path.startswith('media/'):
        file_path = file_path[6:]
    
    # Calculate expiry timestamp
    expires = int(time.time()) + expires_in
    
    # Create signature
    signature = create_signature(file_path, expires)
    
    # Build URL with query params
    media_url = settings.MEDIA_URL.rstrip('/')
    query_params = urlencode({
        'expires': expires,
        'signature': signature
    })
    
    return f"{media_url}/{file_path}?{query_params}"


def create_signature(file_path, expires):
    """
    Create HMAC signature for URL.
    
    Args:
        file_path: File path
        expires: Expiry timestamp
        
    Returns:
        String: HMAC signature (hex)
    """
    secret_key = get_signing_key().encode('utf-8')
    message = f"{file_path}:{expires}".encode('utf-8')
    
    signature = hmac.new(
        secret_key,
        message,
        hashlib.sha256
    ).hexdigest()
    
    return signature


def verify_signed_url(file_path, expires, signature):
    """
    Verify whether signed URL is valid.
    
    Args:
        file_path: Path of requested file
        expires: Expiry timestamp from query param
        signature: Signature from query param
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
        
    Example:
        >>> verify_signed_url('profile.jpg', 1234567890, 'abc123')
        (True, None)  # Valid
        
        >>> verify_signed_url('profile.jpg', 1234567890, 'invalid')
        (False, 'Invalid signature')  # Invalid
    """
    try:
        expires = int(expires)
    except (ValueError, TypeError):
        return False, 'Invalid expires parameter'
    
    # Check if expired
    current_time = int(time.time())
    if current_time > expires:
        return False, 'URL has expired'
    
    # Verify signature
    expected_signature = create_signature(file_path, expires)
    
    # Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(signature, expected_signature):
        return False, 'Invalid signature'
    
    return True, None


def generate_signed_url_django_signer(file_path, expires_in=3600):
    """
    Alternative implementation using Django's built-in TimestampSigner.
    Simpler but results in longer URLs.
    
    Args:
        file_path: Relative path from MEDIA_ROOT
        expires_in: Expiration time in seconds
        
    Returns:
        String: Full URL with signed token
        
    Example:
        >>> generate_signed_url_django_signer('profile.jpg')
        '/media/profile.jpg?token=eyJmaWxlIjoicHJvZmlsZS5qcGciLCJleHBpcmVzIjoxMjM0NTY3ODkwfQ...'
    """
    if not file_path:
        return None
    
    file_path = file_path.lstrip('/').replace('media/', '', 1)
    
    signer = TimestampSigner()
    signed_value = signer.sign(file_path)
    
    media_url = settings.MEDIA_URL.rstrip('/')
    query_params = urlencode({
        'token': signed_value,
        'max_age': expires_in
    })
    
    return f"{media_url}/{file_path}?{query_params}"


def verify_signed_url_django_signer(file_path, token, max_age):
    """
    Verify signed URL created with Django's TimestampSigner.
    
    Args:
        file_path: Path of requested file
        token: Signed token from query param
        max_age: Max age in seconds
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    try:
        max_age = int(max_age)
        signer = TimestampSigner()
        
        # Unsign with max_age check
        original_value = signer.unsign(token, max_age=max_age)
        
        # Verify path matches
        if original_value != file_path:
            return False, 'Token does not match requested file'
        
        return True, None
        
    except SignatureExpired:
        return False, 'URL has expired'
    except BadSignature:
        return False, 'Invalid signature'
    except (ValueError, TypeError):
        return False, 'Invalid parameters'


# Helper function to generate signed URL from FileField
def get_signed_url_from_field(file_field, expires_in=3600):
    """
    Helper to generate signed URL from Django FileField/ImageField.
    
    Args:
        file_field: Django FileField/ImageField instance
        expires_in: Expiration time in seconds
        
    Returns:
        String: Signed URL or None if field is empty
        
    Example:
        >>> user = User.objects.get(id=123)
        >>> signed_url = get_signed_url_from_field(user.photo_profile)
        >>> # Returns: '/media/profile_pictures/user123.jpg?expires=...&signature=...'
    """
    if not file_field:
        return None
    
    try:
        # FileField.name contains relative path from MEDIA_ROOT
        return generate_signed_url(file_field.name, expires_in)
    except Exception:
        return None
