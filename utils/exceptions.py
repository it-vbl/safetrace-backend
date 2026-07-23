from rest_framework.views import exception_handler
from .serializers import custom_response


def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework.
    
    Handles exceptions and wraps them in a custom response format.
    
    Args:
        exc: The exception that was raised.
        context: Additional context information about the exception.
    
    Returns:
        Response: A formatted response object with standardized error structure,
                 or None if the exception is not handled by DRF.
    """
    
    response = exception_handler(exc, context)
    if response is not None:
        # Format default error message from DRF
        if isinstance(response.data, dict) and "detail" in response.data:
            error_message = response.data["detail"]
        else:
            error_message = response.data

        # Re-wrap error response with custom format
        custom_error_response = custom_response("error", error_message, errors=response.data)

        # Update response with custom formatted data
        response.data = custom_error_response
        response.status_code = response.status_code

    return response
