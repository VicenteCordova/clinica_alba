"""apps/tratamientos/urls.py"""
from django.urls import path
from apps.tratamientos import views

app_name = "tratamientos"

urlpatterns = [
    path("", views.TratamientoListView.as_view(), name="lista"),
    path("nuevo/", views.TratamientoCrearView.as_view(), name="crear"),
    path("<int:pk>/editar/", views.TratamientoEditarView.as_view(), name="editar"),
    path("planes/", views.PlanTratamientoListView.as_view(), name="planes"),
    path("planes/<int:pk>/", views.PlanTratamientoDetalleView.as_view(), name="plan_detalle"),
    path("planes/<int:ficha_id>/nuevo/", views.PlanTratamientoCrearView.as_view(), name="plan_crear"),
    path("planes/<int:pk>/cambiar-estado/", views.PlanCambiarEstadoView.as_view(), name="plan_cambiar_estado"),
]
