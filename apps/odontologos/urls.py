"""apps/odontologos/urls.py"""
from django.urls import path
from apps.odontologos import views

app_name = "odontologos"

urlpatterns = [
    path("", views.OdontologoListView.as_view(), name="lista"),
    path("nuevo/", views.OdontologoCrearView.as_view(), name="crear"),
    path("<int:pk>/", views.OdontologoDetalleView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.OdontologoEditarView.as_view(), name="editar"),
]
