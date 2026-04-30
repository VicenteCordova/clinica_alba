"""
apps/caja/urls.py
"""
from django.urls import path
from apps.caja import views

app_name = "caja"

urlpatterns = [
    path("", views.CajaListView.as_view(), name="lista"),
    path("abrir/", views.AbrirCajaView.as_view(), name="abrir"),
    path("<int:pk>/", views.CajaDetalleView.as_view(), name="detalle"),
    path("<int:pk>/cerrar/", views.CerrarCajaView.as_view(), name="cerrar"),
    path("<int:pk>/movimiento/", views.MovimientoCajaView.as_view(), name="movimiento"),
]
