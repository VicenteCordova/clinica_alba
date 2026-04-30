from django.contrib import admin
from django.utils import timezone
from .models import (
    TipoExamenImagenologico,
    ExamenImagenologico,
    ArchivoExamenImagenologico,
    ObservacionImagenologica,
    AccesoExamenImagenologico
)

@admin.register(TipoExamenImagenologico)
class TipoExamenImagenologicoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "estado", "fecha_creacion")
    search_fields = ("nombre",)
    list_filter = ("estado",)

    def delete_model(self, request, obj):
        obj.estado = TipoExamenImagenologico.ESTADO_INACTIVO
        obj.save(update_fields=["estado"])

    def delete_queryset(self, request, queryset):
        queryset.update(estado=TipoExamenImagenologico.ESTADO_INACTIVO)

@admin.register(ExamenImagenologico)
class ExamenImagenologicoAdmin(admin.ModelAdmin):
    list_display = ("id_examen", "paciente", "tipo_examen", "fecha_examen", "estado")
    search_fields = ("paciente__id_persona__nombres", "paciente__id_persona__apellido_paterno", "paciente__id_persona__rut")
    list_filter = ("estado", "tipo_examen", "fecha_examen")
    raw_id_fields = ("paciente", "ficha_clinica", "cita", "evolucion", "creado_por", "solicitado_por")

    def delete_model(self, request, obj):
        obj.estado = ExamenImagenologico.ESTADO_ANULADO
        obj.save(update_fields=["estado"])

    def delete_queryset(self, request, queryset):
        queryset.update(estado=ExamenImagenologico.ESTADO_ANULADO)

@admin.register(ArchivoExamenImagenologico)
class ArchivoExamenImagenologicoAdmin(admin.ModelAdmin):
    list_display = ("id_archivo", "examen", "nombre_original", "extension", "estado", "fecha_subida")
    list_filter = ("estado", "extension")
    raw_id_fields = ("examen", "subido_por", "usuario_responsable", "adjunto_reemplazo")

    def delete_model(self, request, obj):
        obj.estado = ArchivoExamenImagenologico.ESTADO_ANULADO
        obj.motivo_anulacion = "Anulado desde admin"
        obj.fecha_anulacion = timezone.now()
        obj.usuario_responsable = request.user
        obj.save(update_fields=["estado", "motivo_anulacion", "fecha_anulacion", "usuario_responsable"])

    def delete_queryset(self, request, queryset):
        queryset.update(
            estado=ArchivoExamenImagenologico.ESTADO_ANULADO,
            motivo_anulacion="Anulado desde admin",
            fecha_anulacion=timezone.now(),
            usuario_responsable=request.user,
        )

@admin.register(ObservacionImagenologica)
class ObservacionImagenologicaAdmin(admin.ModelAdmin):
    list_display = ("id_observacion", "examen", "usuario", "fecha_observacion")
    raw_id_fields = ("examen", "usuario")

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(AccesoExamenImagenologico)
class AccesoExamenImagenologicoAdmin(admin.ModelAdmin):
    list_display = ("id_acceso", "archivo", "usuario", "accion", "fecha_acceso")
    list_filter = ("accion", "fecha_acceso")
    raw_id_fields = ("archivo", "usuario")

    def has_delete_permission(self, request, obj=None):
        return False
