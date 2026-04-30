"""
apps/auditoria/admin.py
"""
from django.contrib import admin
from apps.auditoria.models import Bitacora


@admin.register(Bitacora)
class BitacoraAdmin(admin.ModelAdmin):
    list_display = [
        "fecha_evento", "get_usuario", "modulo", "accion",
        "tabla_afectada", "id_registro_afectado", "ip_origen"
    ]
    list_filter = ["modulo", "accion"]
    search_fields = ["id_usuario__username", "descripcion", "tabla_afectada"]
    readonly_fields = [f.name for f in Bitacora._meta.fields]

    def get_usuario(self, obj): return obj.id_usuario.username
    get_usuario.short_description = "Usuario"

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
