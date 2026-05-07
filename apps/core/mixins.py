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


from django.contrib.auth.mixins import PermissionRequiredMixin

class PermisoRequeridoMixin(LoginRequeridoMixin, PermissionRequiredMixin):
    """
    Combina LoginRequeridoMixin con PermissionRequiredMixin.
    Muestra un mensaje de error si no se tienen permisos.
    """
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "No tienes permisos para realizar esta acción.")
            # Registrar intento fallido en bitácora si se desea
            from apps.auditoria.models import Bitacora
            Bitacora.registrar(
                usuario=self.request.user,
                modulo="seguridad",
                accion="intento_sin_permiso",
                tabla_afectada="N/A",
                id_registro_afectado=0,
                descripcion=f"Intento de acceso a {self.request.path} sin permisos {self.get_permission_required()}",
                request=self.request
            )
            raise PermissionDenied("No tienes permisos suficientes para acceder a esta sección.")
        return super().handle_no_permission()


from django.views.generic import View
from django.shortcuts import redirect
from django.urls import reverse_lazy

class InhabilitarBaseView(PermisoRequeridoMixin, View):
    """
    Vista base para inhabilitar lógicamente un registro que hereda de InhabilitableModel.
    Debe recibir un POST con el 'motivo'.
    """
    model = None
    url_redirect = None
    modulo_auditoria = "general"
    
    def post(self, request, pk, *args, **kwargs):
        obj = self.model.objects.get(pk=pk)
        motivo = request.POST.get("motivo_inhabilitacion", "").strip()
        
        if not motivo:
            messages.error(request, "Debe proporcionar un motivo para inhabilitar el registro.")
            return redirect(self.url_redirect or request.META.get('HTTP_REFERER', '/'))
            
        obj.inhabilitar(usuario=request.user, motivo=motivo)
        
        from apps.auditoria.models import Bitacora
        Bitacora.registrar(
            usuario=request.user,
            modulo=self.modulo_auditoria,
            accion="inhabilitar",
            tabla_afectada=self.model._meta.db_table,
            id_registro_afectado=pk,
            descripcion=f"Registro inhabilitado: {motivo}",
            request=request
        )
        
        messages.success(request, f"El registro ha sido inhabilitado correctamente.")
        return redirect(self.url_redirect or request.META.get('HTTP_REFERER', '/'))

