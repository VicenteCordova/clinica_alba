"""
apps/core/context_processors.py

Datos globales disponibles en todos los templates.
"""
from django.conf import settings


def clinica_context(request):
    """Inyecta datos de la clinica y del usuario autenticado en todos los templates."""
    ctx = {
        "CLINICA_NOMBRE": settings.CLINICA_NOMBRE,
        "CLINICA_RUT": settings.CLINICA_RUT,
        "CLINICA_DIRECCION": settings.CLINICA_DIRECCION,
        "CLINICA_TELEFONO": settings.CLINICA_TELEFONO,
        "CLINICA_EMAIL": settings.CLINICA_EMAIL,
    }
    if request.user.is_authenticated:
        ctx["usuario_roles"] = list(
            request.user.usuario_roles.filter(rol__estado_rol="activo")
            .values_list("rol__nombre", flat=True)
        )
        # Caja abierta del usuario actual (para topbar)
        try:
            from apps.caja.models import Caja
            ctx["caja_usuario"] = Caja.objects.filter(
                id_usuario_apertura=request.user,
                estado_caja="abierta",
            ).first()
        except Exception:
            ctx["caja_usuario"] = None
    return ctx
