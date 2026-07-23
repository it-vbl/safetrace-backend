from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import BasePermission
from functools import wraps


class RolePermission(BasePermission):
    """
    Permission class for role-based access control.
    
    This class checks whether a user has any of the allowed roles.
    It compares the user's roles with the allowed roles and grants
    permission if there is an intersection.
    """
    
    allowed_roles = []

    def has_permission(self, request, view):
        """
        Check if the user has permission based on their roles.
        
        Args:
            request: The HTTP request object
            view: The view being accessed
            
        Returns:
            bool: True if user has at least one allowed role, False otherwise
        """
        if not hasattr(request.user, 'roles'):
            return False
        
        user_roles = request.user.roles
        # Convert to set with the same type for fast comparison
        try:
            user_roles_set = {int(role) for role in user_roles}
            allowed_roles_set = set(self.allowed_roles)
            has_role = bool(user_roles_set & allowed_roles_set)  # Intersection
        except ValueError:
            return False
        
        print(f"User roles: {user_roles}, Allowed roles: {self.allowed_roles}, Has role: {has_role}")
        return has_role


def role_required(*roles):
    """
    Decorator factory to create a RolePermission class with specific allowed roles.
    
    Args:
        *roles: Variable length argument list of allowed role identifiers
        
    Returns:
        CustomRolePermission: A custom RolePermission class with the specified allowed roles
    """
    class CustomRolePermission(RolePermission):
        allowed_roles = roles

    return CustomRolePermission


def superuser_required(view_func):
    """
    Decorator to require superuser status for accessing a view.
    
    This decorator checks if the user is authenticated and is a superuser.
    If not, it returns an HTTP 403 Forbidden response.
    
    Args:
        view_func: The view function to be wrapped
        
    Returns:
        _wrapped_view: The wrapped view function
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden("You do not have access to this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
