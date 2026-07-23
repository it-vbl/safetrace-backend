from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class UsernameOrEmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using either their username or email address.
    
    This backend extends Django's ModelBackend to support authentication with either a username or email
    combined with a password. It provides a flexible login mechanism for users who may not remember
    their exact username.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user using either their username or email address along with their password.
        
        Args:
            request: The HTTP request object.
            username: The username or email address of the user attempting to log in.
            password: The password associated with the user account.
            **kwargs: Additional keyword arguments (unused).
        
        Returns:
            User: The authenticated User object if credentials are valid, None otherwise.
        
        This method first checks if both username and password are provided. It then attempts to
        find a user by email first, and falls back to searching by username if no email match is found.
        If a user is found, the password is verified before returning the user object.
        """
        if username is None or password is None:
            return None

        try:
            user = User.objects.filter(
                email=username
            ).first() or User.objects.filter(username=username).first()
        except User.DoesNotExist:
            return None

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
