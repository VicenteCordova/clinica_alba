"""
config/urls.py — URLs raíz del proyecto.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin de Django (solo para gestión interna)
    path("admin/", admin.site.urls),

    # ── Apps del sistema ────────────────────────────────────────────────────────
    path("", include("apps.dashboard.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("personas/", include("apps.personas.urls")),
    path("pacientes/", include("apps.pacientes.urls")),
    path("odontologos/", include("apps.odontologos.urls")),
    path("agenda/", include("apps.agenda.urls")),
    path("fichas/", include("apps.fichas.urls")),
    path("antecedentes/", include("apps.antecedentes.urls")),
    path("odontograma/", include("apps.odontograma.urls")),
    path("tratamientos/", include("apps.tratamientos.urls")),
    path("presupuestos/", include("apps.presupuestos.urls")),
    path("pagos/", include("apps.pagos.urls")),
    path("caja/", include("apps.caja.urls")),
    path("auditoria/", include("apps.auditoria.urls")),
    path("imagenologia/", include("apps.imagenologia.urls")),
]

# Servir media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Personalizar admin
admin.site.site_header = "Clínica Odontológica El Alba — Admin"
admin.site.site_title = "El Alba Admin"
admin.site.index_title = "Panel de Administración"
