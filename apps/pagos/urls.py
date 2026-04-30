"""apps/pagos/urls.py"""
from django.urls import path
from apps.pagos import views

app_name = "pagos"

urlpatterns = [
    path("", views.PagoListaView.as_view(), name="lista"),
    path("presupuesto/<int:presupuesto_id>/nuevo/", views.PagoCrearView.as_view(), name="crear"),
    path("<int:pk>/anular/", views.PagoAnularView.as_view(), name="anular"),
]
