"""apps/pacientes/urls.py"""
from django.urls import path
from apps.pacientes import views

app_name = "pacientes"

urlpatterns = [
    path("", views.PacienteListView.as_view(), name="lista"),
    path("nuevo/", views.PacienteCrearView.as_view(), name="crear"),
    path("<int:pk>/", views.PacienteDetalleView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.PacienteEditarView.as_view(), name="editar"),
    path("buscar/", views.PacienteBuscarHTMXView.as_view(), name="buscar_htmx"),
]
