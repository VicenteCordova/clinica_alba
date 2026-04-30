"""
apps/fichas/urls.py
"""
from django.urls import path
from apps.fichas import views

app_name = "fichas"

urlpatterns = [
    path("paciente/<int:paciente_id>/", views.FichaDetalleView.as_view(), name="detalle"),
    path("paciente/<int:paciente_id>/abrir/", views.AbrirFichaView.as_view(), name="abrir"),
    path("paciente/<int:paciente_id>/editar/", views.FichaEditarView.as_view(), name="editar"),
    path("paciente/<int:paciente_id>/cambiar-estado/", views.FichaCambiarEstadoView.as_view(), name="cambiar_estado"),
    path("cita/<int:cita_id>/atencion/", views.AtencionCitaView.as_view(), name="modo_atencion"),
    path("evolucion/<int:cita_id>/crear/", views.EvolucionCrearView.as_view(), name="evolucion_crear"),
    path("evolucion/<int:pk>/", views.EvolucionDetalleView.as_view(), name="evolucion_detalle"),
    path("evolucion/<int:pk>/editar/", views.EvolucionEditarView.as_view(), name="evolucion_editar"),
    path("evolucion/<int:pk>/adjunto/", views.AdjuntoSubirView.as_view(), name="adjunto_subir"),
]
