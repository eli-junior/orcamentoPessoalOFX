"""Backend de autenticação customizado para login com email."""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """Backend que permite autenticação usando email e senha."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """Autentica usuário usando email (passado no campo username)."""
        email = username or kwargs.get('email')
        
        if not email:
            return None
            
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
            
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        """Retorna usuário pelo ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
