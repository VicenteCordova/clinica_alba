"""
apps/accounts/admin.py
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.accounts.models import Rol, Usuario, UsuarioRol


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ["nombre", "descripcion", "estado_rol"]
    list_filter = ["estado_rol"]
    search_fields = ["nombre"]

    def delete_model(self, request, obj):
        obj.estado_rol = Rol.ESTADO_INACTIVO
        obj.save(update_fields=["estado_rol"])

    def delete_queryset(self, request, queryset):
        queryset.update(estado_rol=Rol.ESTADO_INACTIVO)


class UsuarioRolInline(admin.TabularInline):
    model = UsuarioRol
    extra = 1


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ["username", "get_nombre_completo", "estado_acceso", "ultimo_acceso", "is_staff"]
    list_filter = ["estado_acceso", "is_staff"]
    search_fields = ["username", "id_persona__nombres", "id_persona__apellido_paterno"]
    inlines = [UsuarioRolInline]
    readonly_fields = ["ultimo_acceso", "fecha_creacion", "fecha_actualizacion"]

    def get_nombre_completo(self, obj):
        return obj.nombre_completo
    get_nombre_completo.short_description = "Nombre completo"

    def delete_model(self, request, obj):
        obj.estado_acceso = Usuario.ESTADO_INACTIVO
        obj.save(update_fields=["estado_acceso"])

    def delete_queryset(self, request, queryset):
        queryset.update(estado_acceso=Usuario.ESTADO_INACTIVO)
