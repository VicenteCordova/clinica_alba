"""apps/antecedentes/urls.py"""
from django.urls import path
from apps.antecedentes import views

app_name = "antecedentes"

urlpatterns = [
    path("paciente/<int:paciente_id>/", views.AntecedentesPacienteView.as_view(), name="lista"),
    path("paciente/<int:paciente_id>/nuevo/", views.RegistrarAntecedentesView.as_view(), name="registrar"),
    path("<int:pk>/editar/", views.EditarAntecedentesView.as_view(), name="editar"),
    path("catalogo/", views.CatalogoListView.as_view(), name="catalogo"),
]
