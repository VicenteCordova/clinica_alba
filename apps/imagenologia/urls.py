"""
apps/imagenologia/urls.py
"""
from django.urls import path
from . import views

app_name = "imagenologia"

urlpatterns = [
    path("", views.ExamenListView.as_view(), name="lista"),
    path("paciente/<int:paciente_id>/", views.PacienteExamenListView.as_view(), name="paciente_lista"),
    path("nuevo/paciente/<int:paciente_id>/", views.ExamenCrearView.as_view(), name="crear"),
    path("examen/<int:pk>/", views.ExamenDetalleView.as_view(), name="detalle"),
    path("examen/<int:pk>/editar/", views.ExamenEditarView.as_view(), name="editar"),
    path("examen/<int:pk>/archivos/subir/", views.ArchivoSubirView.as_view(), name="subir_archivo"),
    path("examen/<int:pk>/observaciones/nueva/", views.ObservacionCrearView.as_view(), name="crear_observacion"),
    path("archivo/<int:pk>/descargar/", views.ArchivoDescargarView.as_view(), name="descargar_archivo"),
    path("archivo/<int:pk>/ver/", views.ArchivoVerView.as_view(), name="ver_archivo"),
    path("archivo/<int:pk>/eliminar/", views.ArchivoEliminarView.as_view(), name="eliminar_archivo"),
    path("archivo/<int:pk>/reemplazar/", views.ArchivoReemplazarView.as_view(), name="reemplazar_archivo"),

    # Tipos de Examen
    path("tipos/", views.TipoExamenListView.as_view(), name="tipos_lista"),
    path("tipos/nuevo/", views.TipoExamenCrearView.as_view(), name="tipos_crear"),
    path("tipos/<int:pk>/editar/", views.TipoExamenEditarView.as_view(), name="tipos_editar"),
]
