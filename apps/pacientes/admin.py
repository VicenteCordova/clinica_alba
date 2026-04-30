"""
apps/pacientes/admin.py
"""
from django.contrib import admin
from apps.pacientes.models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ["get_rut", "get_nombre", "get_correo", "fecha_registro"]
    search_fields = ["id_persona__rut", "id_persona__nombres", "id_persona__apellido_paterno"]
    readonly_fields = ["fecha_registro"]

    def get_rut(self, obj): return obj.rut
    get_rut.short_description = "RUT"

    def get_nombre(self, obj): return obj.nombre_completo
    get_nombre.short_description = "Nombre"

    def get_correo(self, obj): return obj.id_persona.correo
    get_correo.short_description = "Correo"

    def delete_model(self, request, obj):
        obj.id_persona.estado_persona = "inactivo"
        obj.id_persona.save(update_fields=["estado_persona"])

    def delete_queryset(self, request, queryset):
        from apps.personas.models import Persona
        Persona.objects.filter(paciente__in=queryset).update(estado_persona="inactivo")
