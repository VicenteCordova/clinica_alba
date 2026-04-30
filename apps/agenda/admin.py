"""
apps/agenda/admin.py
"""
from django.contrib import admin
from apps.agenda.models import Box, TipoAtencion, EstadoCita, Cita, HistorialCita


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ["nombre", "ubicacion", "estado_box"]
    list_filter = ["estado_box"]

    def delete_model(self, request, obj):
        obj.estado_box = Box.ESTADO_INACTIVO
        obj.save(update_fields=["estado_box"])

    def delete_queryset(self, request, queryset):
        queryset.update(estado_box=Box.ESTADO_INACTIVO)


@admin.register(TipoAtencion)
class TipoAtencionAdmin(admin.ModelAdmin):
    list_display = ["nombre", "duracion_estimada_min", "estado_tipo_atencion"]

    def delete_model(self, request, obj):
        obj.estado_tipo_atencion = TipoAtencion.ESTADO_INACTIVO
        obj.save(update_fields=["estado_tipo_atencion"])

    def delete_queryset(self, request, queryset):
        queryset.update(estado_tipo_atencion=TipoAtencion.ESTADO_INACTIVO)


@admin.register(EstadoCita)
class EstadoCitaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "descripcion"]


class HistorialCitaInline(admin.TabularInline):
    model = HistorialCita
    extra = 0
    readonly_fields = ["id_estado_anterior", "id_estado_nuevo", "fecha_cambio", "id_usuario_responsable"]


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = [
        "id_cita", "get_paciente", "get_odontologo",
        "fecha_hora_inicio", "id_estado_cita", "id_box"
    ]
    list_filter = ["id_estado_cita", "id_box", "id_odontologo"]
    search_fields = [
        "id_paciente__id_persona__nombres",
        "id_paciente__id_persona__apellido_paterno",
    ]
    inlines = [HistorialCitaInline]
    readonly_fields = ["fecha_creacion", "fecha_actualizacion"]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_paciente(self, obj): return obj.id_paciente.nombre_completo
    get_paciente.short_description = "Paciente"

    def get_odontologo(self, obj): return obj.id_odontologo.nombre_completo
    get_odontologo.short_description = "Odontólogo"
