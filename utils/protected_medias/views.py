"""
Protected Media Views
Utilities for serving media files with authentication and permission checks.

Usage:
    # Basic usage - require login only
    path('protected-media/<path:file_path>', ProtectedMediaView.as_view(), name='protected_media')
    
    # Custom permission check
    class CustomProtectedMediaView(ProtectedMediaView):
        def check_permission(self, request, file_path):
            # Custom logic
            if not request.user.has_perm('app.view_something'):
                return False
            return super().check_permission(request, file_path)
"""
import os
import mimetypes
from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.views import View
from django.utils.encoding import escape_uri_path

# Signed URL support
from .signed_url import verify_signed_url

# Django REST Framework imports for JWT authentication
try:
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from rest_framework.exceptions import AuthenticationFailed
    HAS_JWT = True
except ImportError:
    HAS_JWT = False


class ProtectedMediaView(View):
    """
    View for serving protected media files with support for:
    - Signed URLs (temporary URLs with signature & expiry) - PRIORITY #1
    - JWT Authentication (for API/Frontend with Bearer token)
    - Django Session Authentication (for Admin/Web)
    
    By default, only requires login. Can be overridden for custom permission checks.
    
    Features:
    - Signed URL support (expires & signature validation)
    - JWT Bearer token support (Authorization: Bearer <token>)
    - Django session/cookie authentication fallback
    - Custom permission check support
    - X-Accel-Redirect support for production (Nginx)
    - Proper content-type detection
    - Range request support (for video/audio streaming)
    """
    
    # Set True to use X-Accel-Redirect (Nginx production)
    use_xaccel = False
    
    # Prefix for X-Accel-Redirect (adjust to match Nginx config)
    xaccel_redirect_prefix = '/protected'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to handle authentication before routing to method handler.
        
        Authentication Priority:
        1. Signed URL (query params: expires & signature)
        2. JWT Token (Authorization: Bearer <token>)
        3. Django Session (cookies)
        """
        file_path = kwargs.get('file_path', '')
        
        # Try Signed URL authentication first (least intrusive for frontend)
        if self.has_signed_url_params(request):
            is_valid, error = self.verify_signed_url_params(request, file_path)
            if is_valid:
                # Signed URL valid - set anonymous user but mark as authenticated
                request._signed_url_authenticated = True
                return super().dispatch(request, *args, **kwargs)
            else:
                # Signed URL invalid - return error
                return JsonResponse({
                    'error': 'Invalid or expired URL',
                    'detail': error
                }, status=401)
        
        # Try JWT or Session authentication
        auth_result = self.authenticate_request(request)
        
        if not auth_result:
            # Return 401 Unauthorized
            return JsonResponse({
                'error': 'Authentication credentials were not provided or are invalid.',
                'detail': 'Please provide valid JWT token, signed URL, or login via session.'
            }, status=401)
        
        # Continue to method handler (get, post, etc.)
        return super().dispatch(request, *args, **kwargs)
    
    def has_signed_url_params(self, request):
        """
        Check if request has signed URL parameters.
        
        Args:
            request: HTTP request object
            
        Returns:
            Boolean: True if expires & signature params are present
        """
        return 'expires' in request.GET and 'signature' in request.GET
    
    def verify_signed_url_params(self, request, file_path):
        """
        Verify signed URL parameters.
        
        Args:
            request: HTTP request object
            file_path: Requested file path
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        expires = request.GET.get('expires')
        signature = request.GET.get('signature')
        
        return verify_signed_url(file_path, expires, signature)
    
    def authenticate_request(self, request):
        """
        Authenticate request using JWT or Django session.
        
        Priority:
        1. JWT Token (Authorization: Bearer <token>)
        2. Django Session (cookies)
        
        Args:
            request: HTTP request object
            
        Returns:
            Boolean: True if authenticated, False otherwise
        """
        # Try JWT authentication first (for frontend/API)
        if HAS_JWT and self.has_jwt_token(request):
            try:
                jwt_auth = JWTAuthentication()
                result = jwt_auth.authenticate(request)
                
                if result is not None:
                    user, token = result
                    request.user = user
                    request.auth = token
                    return True
            except (AuthenticationFailed, Exception):
                # JWT authentication failed, try session auth
                pass
        
        # Fallback to Django session authentication (for admin/web)
        if hasattr(request, 'user') and request.user.is_authenticated:
            return True
        
        return False
    
    def has_jwt_token(self, request):
        """
        Check if request has JWT token in Authorization header.
        
        Args:
            request: HTTP request object
            
        Returns:
            Boolean: True if JWT token is present
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        return auth_header.startswith('Bearer ')
    
    def get(self, request, file_path):
        """
        Handle GET request to serve file.
        
        Args:
            request: HTTP request object
            file_path: Relative path from MEDIA_ROOT
            
        Returns:
            FileResponse or HttpResponse (if X-Accel)
        """
        # Check custom permission
        if not self.check_permission(request, file_path):
            return JsonResponse({
                'error': 'Permission denied',
                'detail': 'You do not have permission to access this file.'
            }, status=403)
        
        # Construct full file path
        full_path = self.get_file_path(file_path)
        
        # Check file exists
        if not os.path.exists(full_path):
            raise Http404("File not found")
        
        # Check if file is really inside MEDIA_ROOT (security check)
        if not self.is_safe_path(full_path):
            raise Http404("Access denied")
        
        # Use X-Accel-Redirect for production (faster, handled by Nginx)
        if self.should_use_xaccel():
            return self.xaccel_redirect_response(file_path)
        
        # Serve file directly through Django (development)
        return self.serve_file(full_path)
    
    def check_permission(self, request, file_path):
        """
        Check if user has permission to access file.
        Override this method for custom permission logic.
        
        Args:
            request: HTTP request object
            file_path: Relative path from MEDIA_ROOT
            
        Returns:
            Boolean: True if allowed, False otherwise
            
        Example:
            def check_permission(self, request, file_path):
                # Example: only owner can access their profile picture
                if 'profile_pictures/' in file_path:
                    username = file_path.split('/')[1]
                    return request.user.username == username
                return True
        """
        # Signed URL already validated - allow access
        if getattr(request, '_signed_url_authenticated', False):
            return True
        
        # Regular authentication - check if user is authenticated
        return hasattr(request, 'user') and request.user.is_authenticated
    
    def get_file_path(self, file_path):
        """
        Construct full file path from MEDIA_ROOT and relative path.
        
        Args:
            file_path: Relative path from MEDIA_ROOT
            
        Returns:
            String: Full absolute path to file
        """
        media_root = Path(settings.MEDIA_ROOT)
        full_path = media_root / file_path
        return str(full_path.resolve())
    
    def is_safe_path(self, full_path):
        """
        Security check: ensure file path is inside MEDIA_ROOT.
        Prevents directory traversal attacks (e.g., ../../etc/passwd)
        
        Args:
            full_path: Full absolute path to check
            
        Returns:
            Boolean: True if safe, False if dangerous
        """
        media_root = Path(settings.MEDIA_ROOT).resolve()
        file_path = Path(full_path).resolve()
        
        try:
            file_path.relative_to(media_root)
            return True
        except ValueError:
            # Path is outside MEDIA_ROOT
            return False
    
    def should_use_xaccel(self):
        """
        Determine whether to use X-Accel-Redirect.
        Check settings and instance variable.
        
        Returns:
            Boolean: True if X-Accel should be used
        """
        # Check from settings (can be set in prod.py: PROTECTED_MEDIA_USE_XACCEL = True)
        use_xaccel_setting = getattr(settings, 'PROTECTED_MEDIA_USE_XACCEL', False)
        return self.use_xaccel or use_xaccel_setting
    
    def xaccel_redirect_response(self, file_path):
        """
        Return HttpResponse with X-Accel-Redirect header.
        Nginx will serve the file, more efficient for production.
        
        Nginx config example:
            location /protected {
                internal;
                alias /path/to/media/;
            }
        
        Args:
            file_path: Relative path from MEDIA_ROOT
            
        Returns:
            HttpResponse with X-Accel-Redirect header
        """
        # Get prefix from settings or instance variable
        prefix = getattr(
            settings, 
            'PROTECTED_MEDIA_XACCEL_PREFIX',
            self.xaccel_redirect_prefix
        )
        
        # Construct X-Accel-Redirect path
        redirect_path = f"{prefix}/{file_path}"
        
        # Detect content type
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Return empty response with X-Accel-Redirect header
        response = HttpResponse()
        response['X-Accel-Redirect'] = escape_uri_path(redirect_path)
        response['Content-Type'] = content_type
        
        return response
    
    def serve_file(self, full_path):
        """
        Serve file directly through Django (for development).
        Support range requests for streaming.
        
        Args:
            full_path: Full absolute path to file
            
        Returns:
            FileResponse
        """
        # Detect content type
        content_type, _ = mimetypes.guess_type(full_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Open file and return FileResponse
        # FileResponse automatically handles:
        # - Range requests (for streaming)
        # - Proper headers (Content-Length, etc.)
        # - Chunked transfer
        response = FileResponse(
            open(full_path, 'rb'),
            content_type=content_type
        )
        
        # Set filename for download
        filename = os.path.basename(full_path)
        response['Content-Disposition'] = f'inline; filename="{escape_uri_path(filename)}"'
        
        return response


class ProtectedMediaDownloadView(ProtectedMediaView):
    """
    Variant of ProtectedMediaView that forces file download
    (Content-Disposition: attachment) instead of inline display.
    """
    
    def serve_file(self, full_path):
        """Override to force download"""
        response = super().serve_file(full_path)
        
        # Change from inline to attachment
        filename = os.path.basename(full_path)
        response['Content-Disposition'] = f'attachment; filename="{escape_uri_path(filename)}"'
        
        return response


# Example: Custom permission for specific use case
class PekebunMediaView(ProtectedMediaView):
    """
    Protected media view specific for farmer (pekebun) data.
    Can customize permission logic according to needs.
    """
    
    def check_permission(self, request, file_path):
        """
        Custom logic for farmer media files.
        Example: admin can access all, regular users can only access their own data.
        """
        # Admin/staff can access all
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # TODO: Implement logic to check ownership
        # Example: check if this file belongs to the currently logged-in user
        # if 'profile_pictures/' in file_path:
        #     pekebun = get_object_or_404(Pekebun, user=request.user)
        #     return str(pekebun.foto_profile) == file_path
        
        # Default: allow if already logged in
        return super().check_permission(request, file_path)
