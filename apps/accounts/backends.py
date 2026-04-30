"""
apps/accounts/backends.py

Backend de autenticación custom que valida contra la tabla `usuarios`
y verifica el estado_acceso antes de permitir el acceso.
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password


class CustomAuthBackend(BaseBackend):
    """
    Autentica usando username + password_hash de la tabla `usuarios`.
    Bloquea usuarios con estado_acceso distinto de 'activo'.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        from apps.accounts.models import Usuario

        if not username or not password:
            return None

        try:
            usuario = Usuario.objects.select_related("id_persona").get(
                username=username
            )
        except Usuario.DoesNotExist:
            # Ejecutar una comparación dummy para evitar timing attacks
            check_password(password, "!")
            return None

        if usuario.estado_acceso != Usuario.ESTADO_ACTIVO:
            return None

        if not usuario.check_password(password):
            return None

        return usuario

    def get_user(self, user_id):
        from apps.accounts.models import Usuario

        try:
            return Usuario.objects.select_related("id_persona").get(pk=user_id)
        except Usuario.DoesNotExist:
            return None
