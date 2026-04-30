"""apps/personas/urls.py"""
from django.urls import path
from apps.personas import views

app_name = "personas"

urlpatterns = [
    path("", views.PersonaListView.as_view(), name="lista"),
    path("nuevo/", views.PersonaCrearView.as_view(), name="crear"),
    path("<int:pk>/", views.PersonaDetalleView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.PersonaEditarView.as_view(), name="editar"),
]
