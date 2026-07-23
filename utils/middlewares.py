from django.conf import settings


class MediaURLMiddleware:
    """
    Middleware to ensure MEDIA_URL uses the correct protocol based on the 
    incoming request (http or https).
    
    This middleware dynamically adjusts the MEDIA_URL protocol to match the 
    configured MEDIA_FORCE_HTTPS setting, ensuring consistent media serving 
    across different request protocols.
    """
    def __init__(self, get_response):
        """
        Initialize the middleware with the next middleware/view handler.
        
        Args:
            get_response: The next middleware or view callable in the chain.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the incoming request and set the media URL with the appropriate protocol.
        
        Args:
            request: The incoming HTTP request object.
            
        Returns:
            The response from the next middleware/view in the chain.
        """
        # Set media URL with the appropriate protocol
        if settings.MEDIA_FORCE_HTTPS:
            # If MEDIA_FORCE_HTTPS is enabled, ensure MEDIA_URL uses HTTPS protocol
            settings.MEDIA_URL = settings.MEDIA_HOST.replace('http://', 'https://') + '/media/'
        
        response = self.get_response(request)
        return response
