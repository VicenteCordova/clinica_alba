"""apps/odontograma/urls.py"""
from django.urls import path
from apps.odontograma import views

app_name = "odontograma"

urlpatterns = [
    path("ficha/<int:ficha_id>/nuevo/", views.OdontogramaCrearView.as_view(), name="crear"),
    path("<int:pk>/", views.OdontogramaDetalleView.as_view(), name="detalle"),
    path("<int:pk>/guardar/", views.OdontogramaDetalleGuardarView.as_view(), name="guardar_detalle"),
    path("api/<int:odontograma_id>/descripcion/", views.OdontogramaDescripcionAPIView.as_view(), name="api_descripcion"),
    path("api/<int:odontograma_id>/pieza/<str:codigo_pieza>/", views.OdontogramaPiezaAPIView.as_view(), name="api_pieza"),
    path("api/<int:odontograma_id>/pieza/<str:codigo_pieza>/estado/", views.OdontogramaActualizarEstadoAPIView.as_view(), name="api_estado"),
    path("api/<int:odontograma_id>/pieza/<str:codigo_pieza>/superficie/", views.OdontogramaActualizarSuperficieAPIView.as_view(), name="api_superficie"),
    path("api/<int:odontograma_id>/pieza/<str:codigo_pieza>/raiz/", views.OdontogramaActualizarRaizAPIView.as_view(), name="api_raiz"),
    path("api/<int:odontograma_id>/pieza/<str:codigo_pieza>/periodonto/", views.OdontogramaActualizarPeriodontoAPIView.as_view(), name="api_periodonto"),
    path("api/<int:odontograma_id>/enviar-plan/", views.OdontogramaEnviarPlanAPIView.as_view(), name="api_enviar_plan"),
]
