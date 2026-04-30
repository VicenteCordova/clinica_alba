"""
apps/core/mixins.py

Mixins reutilizables para vistas basadas en clase.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages


class LoginRequeridoMixin(LoginRequiredMixin):
    """
    Igual que LoginRequiredMixin pero con mensaje humanizado en espanol.
    """
    login_url = "accounts:login"

    def handle_no_permission(self):
        messages.warning(
            self.request,
            "Debes iniciar sesion para acceder a esta seccion."
        )
        return super().handle_no_permission()


class RolRequeridoMixin(LoginRequeridoMixin):
    """
    Restringe el acceso segun los roles del usuario.
    Uso:
        roles_permitidos = ['administrador', 'recepcionista']
    """
    roles_permitidos: list[str] = []

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.tiene_rol(*self.roles_permitidos):
            raise PermissionDenied(
                "No tienes permisos suficientes para acceder a esta seccion."
            )
        return super().dispatch(request, *args, **kwargs)


class ActivoRequeridoMixin(LoginRequeridoMixin):
    """
    Verifica que el usuario tenga estado_acceso = 'activo'.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.estado_acceso != "activo":
            messages.error(request, "Tu cuenta esta bloqueada o inactiva.")
            from django.contrib.auth import logout
            logout(request)
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
