"""
apps/personas/admin.py
"""
from django.contrib import admin
from apps.personas.models import Sexo, Persona


@admin.register(Sexo)
class SexoAdmin(admin.ModelAdmin):
    list_display = ["id_sexo", "nombre"]


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ["rut", "nombre_completo", "correo", "telefono", "estado_persona"]
    list_filter = ["estado_persona", "id_sexo"]
    search_fields = ["rut", "nombres", "apellido_paterno", "correo"]
    readonly_fields = ["fecha_creacion", "fecha_actualizacion"]

    def delete_model(self, request, obj):
        obj.estado_persona = Persona.ESTADO_INACTIVO
        obj.save(update_fields=["estado_persona"])

    def delete_queryset(self, request, queryset):
        queryset.update(estado_persona=Persona.ESTADO_INACTIVO)
