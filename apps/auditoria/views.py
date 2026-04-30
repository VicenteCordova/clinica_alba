"""apps/auditoria/views.py"""
from django.views.generic import ListView
from apps.core.mixins import LoginRequeridoMixin, RolRequeridoMixin
from apps.auditoria.models import Bitacora


class BitacoraListView(RolRequeridoMixin, ListView):
    template_name = "auditoria/lista.html"
    context_object_name = "registros"
    paginate_by = 50
    roles_permitidos = ["administrador", "director", "director_clinico", "auditor"]
    queryset = (
        Bitacora.objects.select_related("id_usuario__id_persona")
        .order_by("-fecha_evento")
    )

    MODULOS = ["accounts", "pacientes", "agenda", "fichas", "caja",
               "pagos", "presupuestos", "tratamientos", "antecedentes", "odontograma",
               "imagenologia"]
    ACCIONES = ["login", "logout", "creacion", "edicion", "eliminacion",
                "cambio_estado", "apertura", "cierre", "movimiento",
                "inicio_atencion", "finalizacion_atencion", "visualizacion",
                "descarga", "subida_archivo", "anulacion", "acceso_denegado"]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        modulo = self.request.GET.get("modulo", "")
        accion = self.request.GET.get("accion", "")
        if q:
            qs = qs.filter(descripcion__icontains=q)
        if modulo:
            qs = qs.filter(modulo=modulo)
        if accion:
            qs = qs.filter(accion=accion)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modulos_disponibles"] = self.MODULOS
        ctx["acciones_disponibles"] = self.ACCIONES
        return ctx
