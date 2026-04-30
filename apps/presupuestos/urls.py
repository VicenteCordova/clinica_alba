"""apps/presupuestos/urls.py"""
from django.urls import path
from apps.presupuestos import views

app_name = "presupuestos"

urlpatterns = [
    path("", views.PresupuestoListView.as_view(), name="lista"),
    path("<int:pk>/", views.PresupuestoDetalleView.as_view(), name="detalle"),
    path("plan/<int:plan_id>/emitir/", views.PresupuestoEmitirView.as_view(), name="emitir"),
    path("<int:pk>/imprimir/", views.PresupuestoImprimirView.as_view(), name="imprimir"),
    path("<int:pk>/cambiar-estado/", views.PresupuestoCambiarEstadoView.as_view(), name="cambiar_estado"),
]
