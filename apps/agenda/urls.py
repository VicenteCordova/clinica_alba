"""apps/agenda/urls.py"""
from django.urls import path
from apps.agenda import views

app_name = "agenda"

urlpatterns = [
    path("", views.CalendarioView.as_view(), name="calendario"),
    path("citas/json/", views.CitasJsonView.as_view(), name="citas_json"),
    path("citas/nueva/", views.CitaCrearView.as_view(), name="crear_cita"),
    path("citas/<int:pk>/", views.CitaDetalleView.as_view(), name="detalle_cita"),
    path("citas/<int:pk>/editar/", views.CitaEditarView.as_view(), name="editar_cita"),
    path(
        "citas/<int:pk>/cambiar-estado/",
        views.CitaCambiarEstadoView.as_view(),
        name="cambiar_estado_cita",
    ),
    path(
        "citas/<int:pk>/cambiar-estado-htmx/<str:nuevo_estado>/",
        views.CitaCambiarEstadoHTMXView.as_view(),
        name="cambiar_estado_htmx",
    ),
]
