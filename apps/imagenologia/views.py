"""
apps/imagenologia/views.py
"""
import os
import mimetypes
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import FileResponse, Http404
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from .models import (
    ExamenImagenologico, ArchivoExamenImagenologico, 
    ObservacionImagenologica, AccesoExamenImagenologico
)
from .forms import ExamenForm, MultipleArchivoForm, validar_archivo_clinico
from apps.pacientes.models import Paciente
from apps.auditoria.models import Bitacora
from apps.core.permissions import puede_editar_imagenologia, puede_ver_imagenologia


class ImagenologiaPermisoMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not puede_ver_imagenologia(request.user):
            Bitacora.registrar(
                usuario=request.user,
                modulo="imagenologia",
                accion="acceso_denegado",
                tabla_afectada="imagenologia_examenes",
                id_registro_afectado=kwargs.get("pk") or kwargs.get("paciente_id") or "-",
                descripcion="Acceso denegado a imagenologia",
                request=request,
            )
            raise PermissionDenied("No tienes permisos para acceder a imagenologia.")
        return super().dispatch(request, *args, **kwargs)


def _odontologo_usuario(usuario):
    try:
        return usuario.odontologo
    except Exception:
        return None


def _atencion_cerrada(examen):
    if not examen.cita_id:
        return False
    try:
        estado = examen.cita.id_estado_cita.nombre.lower()
    except Exception:
        return False
    return estado in {"atendida", "finalizada", "finalizado", "cerrada", "cerrado"}


def _validar_edicion_imagenologia(usuario, examen):
    if not puede_editar_imagenologia(usuario):
        raise PermissionDenied("No tienes permisos para modificar imagenologia clinica.")
    if _atencion_cerrada(examen) and not usuario.tiene_rol(
        "administrador", "director", "director_clinico"
    ):
        raise PermissionDenied("La atencion esta cerrada; no se pueden modificar adjuntos.")


def _validar_gestion_archivo(usuario, archivo):
    _validar_edicion_imagenologia(usuario, archivo.examen)
    if usuario.tiene_rol("administrador", "director", "director_clinico", "imagenologia"):
        return
    if archivo.subido_por_id != usuario.id_usuario:
        raise PermissionDenied("Solo puedes gestionar adjuntos que subiste durante la atencion.")


def _crear_archivo_examen(examen, archivo_subido, usuario, es_principal=False):
    ext = os.path.splitext(archivo_subido.name)[1].lower()
    mime = mimetypes.guess_type(archivo_subido.name)[0] or 'application/octet-stream'
    return ArchivoExamenImagenologico.objects.create(
        examen=examen,
        archivo=archivo_subido,
        nombre_original=archivo_subido.name,
        extension=ext,
        tipo_mime=mime,
        peso_bytes=archivo_subido.size,
        subido_por=usuario,
        es_principal=es_principal,
    )


class ExamenListView(ImagenologiaPermisoMixin, ListView):
    model = ExamenImagenologico
    template_name = "imagenologia/examen_list.html"
    context_object_name = "examenes"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related("paciente__id_persona", "tipo_examen", "solicitado_por__id_usuario__id_persona")
        return qs


class PacienteExamenListView(ImagenologiaPermisoMixin, View):
    template_name = "imagenologia/examen_paciente_list.html"

    def get(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        examenes = ExamenImagenologico.objects.filter(paciente=paciente).select_related("tipo_examen").order_by("-fecha_examen")
        return render(request, self.template_name, {
            "paciente": paciente,
            "examenes": examenes
        })


class ExamenCrearView(ImagenologiaPermisoMixin, View):
    template_name = "imagenologia/examen_form.html"

    def get(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        form = ExamenForm()
        archivo_form = MultipleArchivoForm()
        return render(request, self.template_name, {
            "form": form,
            "archivo_form": archivo_form,
            "paciente": paciente,
            "accion": "Crear",
            "cita_id": request.GET.get("cita", ""),
            "evolucion_id": request.GET.get("evolucion", ""),
        })

    def post(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        form = ExamenForm(request.POST)
        archivo_form = MultipleArchivoForm(request.POST, request.FILES)

        if form.is_valid() and archivo_form.is_valid():
            with transaction.atomic():
                examen = form.save(commit=False)
                examen.paciente = paciente
                examen.ficha_clinica = getattr(paciente, "ficha_clinica", None)
                examen.creado_por = request.user
                examen.solicitado_por = _odontologo_usuario(request.user)
                cita_id = request.POST.get("cita_id")
                evolucion_id = request.POST.get("evolucion_id")
                if cita_id:
                    examen.cita_id = cita_id
                if evolucion_id:
                    examen.evolucion_id = evolucion_id
                examen.save()

                archivos = archivo_form.cleaned_data.get('archivos', [])
                for idx, arch in enumerate(archivos):
                    _crear_archivo_examen(examen, arch, request.user, es_principal=(idx == 0))

                Bitacora.registrar(
                    usuario=request.user, modulo="imagenologia", accion="creacion",
                    tabla_afectada="imagenologia_examenes", id_registro_afectado=examen.id_examen,
                    descripcion=f"Creado examen {examen.tipo_examen.nombre} para paciente {paciente.nombre_completo}",
                    request=request,
                    paciente=paciente,
                    cita=examen.cita,
                )

            messages.success(request, "Examen creado correctamente.")
            return redirect("imagenologia:detalle", pk=examen.id_examen)

        return render(request, self.template_name, {
            "form": form,
            "archivo_form": archivo_form,
            "paciente": paciente,
            "accion": "Crear",
            "cita_id": request.POST.get("cita_id", ""),
            "evolucion_id": request.POST.get("evolucion_id", ""),
        })


class ExamenDetalleView(ImagenologiaPermisoMixin, DetailView):
    model = ExamenImagenologico
    template_name = "imagenologia/examen_detail.html"
    context_object_name = "examen"

    def get_queryset(self):
        return super().get_queryset().select_related("paciente__id_persona", "tipo_examen", "creado_por__id_persona")

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        Bitacora.registrar(
            usuario=request.user,
            modulo="imagenologia",
            accion="visualizacion",
            tabla_afectada="imagenologia_examenes",
            id_registro_afectado=self.object.id_examen,
            descripcion=f"Visualizado examen {self.object.tipo_examen.nombre}",
            request=request,
            paciente=self.object.paciente,
            cita=self.object.cita,
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["archivos"] = self.object.archivos.filter(estado="activo")
        context["observaciones"] = self.object.observaciones.select_related("usuario__id_persona").all()
        return context


class ArchivoDescargarView(ImagenologiaPermisoMixin, View):
    """
    Vista segura para descargar archivos. 
    Asegura que el archivo no esté accesible directamente por URL pública.
    """
    def get(self, request, pk):
        archivo = get_object_or_404(ArchivoExamenImagenologico, pk=pk, estado="activo")
        
        # Validar permisos (ej. solo el médico tratante, o admin)
        # TODO: Añadir lógica de permisos más granular
        
        # Auditoría
        AccesoExamenImagenologico.objects.create(
            archivo=archivo,
            usuario=request.user,
            accion="descarga",
            ip_usuario=getattr(request, "ip_origen", None)
        )
        Bitacora.registrar(
            usuario=request.user,
            modulo="imagenologia",
            accion="descarga",
            tabla_afectada="imagenologia_archivos",
            id_registro_afectado=archivo.id_archivo,
            descripcion=f"Descarga de archivo {archivo.nombre_original}",
            request=request,
            paciente=archivo.examen.paciente,
            cita=archivo.examen.cita,
        )

        try:
            response = FileResponse(archivo.archivo.open('rb'))
            response['Content-Disposition'] = f'attachment; filename="{archivo.nombre_original}"'
            return response
        except FileNotFoundError:
            raise Http404("El archivo físico no se encuentra en el servidor.")


class ArchivoVerView(ImagenologiaPermisoMixin, View):
    """Visualizacion inline segura para imagenes y PDF."""

    def get(self, request, pk):
        archivo = get_object_or_404(ArchivoExamenImagenologico, pk=pk, estado="activo")
        AccesoExamenImagenologico.objects.create(
            archivo=archivo,
            usuario=request.user,
            accion="visualizacion",
            ip_usuario=getattr(request, "ip_origen", None),
        )
        Bitacora.registrar(
            usuario=request.user,
            modulo="imagenologia",
            accion="visualizacion",
            tabla_afectada="imagenologia_archivos",
            id_registro_afectado=archivo.id_archivo,
            descripcion=f"Visualizacion de archivo {archivo.nombre_original}",
            request=request,
            paciente=archivo.examen.paciente,
            cita=archivo.examen.cita,
        )
        try:
            response = FileResponse(archivo.archivo.open("rb"), content_type=archivo.tipo_mime)
            response["Content-Disposition"] = f'inline; filename="{archivo.nombre_original}"'
            return response
        except FileNotFoundError:
            raise Http404("El archivo fisico no se encuentra en el servidor.")


class ExamenEditarView(ImagenologiaPermisoMixin, View):
    template_name = "imagenologia/examen_form.html"

    def get(self, request, pk):
        examen = get_object_or_404(ExamenImagenologico, pk=pk)
        _validar_edicion_imagenologia(request.user, examen)
        form = ExamenForm(instance=examen)
        return render(request, self.template_name, {
            "form": form,
            "paciente": examen.paciente,
            "accion": "Editar",
            "examen": examen
        })

    def post(self, request, pk):
        examen = get_object_or_404(ExamenImagenologico, pk=pk)
        _validar_edicion_imagenologia(request.user, examen)
        form = ExamenForm(request.POST, instance=examen)
        if form.is_valid():
            examen = form.save()
            Bitacora.registrar(
                usuario=request.user,
                modulo="imagenologia",
                accion="edicion",
                tabla_afectada="imagenologia_examenes",
                id_registro_afectado=examen.id_examen,
                descripcion=f"Examen {examen.id_examen} actualizado",
                request=request,
                paciente=examen.paciente,
                cita=examen.cita,
            )
            messages.success(request, "Examen actualizado correctamente.")
            return redirect("imagenologia:detalle", pk=examen.id_examen)
        
        return render(request, self.template_name, {
            "form": form,
            "paciente": examen.paciente,
            "accion": "Editar",
            "examen": examen
        })


class ArchivoSubirView(ImagenologiaPermisoMixin, View):
    def post(self, request, pk):
        examen = get_object_or_404(ExamenImagenologico, pk=pk)
        _validar_edicion_imagenologia(request.user, examen)
        archivo_form = MultipleArchivoForm(request.POST, request.FILES)
        
        if archivo_form.is_valid():
            archivos = archivo_form.cleaned_data.get('archivos', [])
            for arch in archivos:
                _crear_archivo_examen(examen, arch, request.user)
            Bitacora.registrar(
                usuario=request.user,
                modulo="imagenologia",
                accion="subida_archivo",
                tabla_afectada="imagenologia_archivos",
                id_registro_afectado=examen.id_examen,
                descripcion=f"Subidos {len(archivos)} archivo(s) a examen {examen.id_examen}",
                request=request,
                paciente=examen.paciente,
                cita=examen.cita,
            )
            messages.success(request, f"Se subieron {len(archivos)} archivo(s) exitosamente.")
        else:
            messages.error(request, "Error al subir archivos. Verifica el formato y tamaño.")
            
        return redirect("imagenologia:detalle", pk=examen.id_examen)


class ArchivoEliminarView(ImagenologiaPermisoMixin, View):
    def post(self, request, pk):
        archivo = get_object_or_404(ArchivoExamenImagenologico, pk=pk)
        _validar_gestion_archivo(request.user, archivo)
        motivo = request.POST.get("motivo_anulacion", "").strip()
        if not motivo:
            messages.error(request, "Debes indicar el motivo de anulacion del adjunto.")
            return redirect("imagenologia:detalle", pk=archivo.examen_id)
        archivo.estado = ArchivoExamenImagenologico.ESTADO_ANULADO
        archivo.motivo_anulacion = motivo
        archivo.fecha_anulacion = timezone.now()
        archivo.usuario_responsable = request.user
        archivo.save(update_fields=[
            "estado",
            "motivo_anulacion",
            "fecha_anulacion",
            "usuario_responsable",
        ])
        Bitacora.registrar(
            usuario=request.user,
            modulo="imagenologia",
            accion="eliminacion_logica",
            tabla_afectada="imagenologia_archivos",
            id_registro_afectado=archivo.id_archivo,
            descripcion=f"Archivo {archivo.nombre_original} anulado logicamente",
            request=request,
            paciente=archivo.examen.paciente,
            cita=archivo.examen.cita,
            datos_nuevos={"estado": archivo.estado, "motivo": motivo},
        )
        messages.success(request, f"Archivo {archivo.nombre_original} anulado logicamente.")
        return redirect("imagenologia:detalle", pk=archivo.examen_id)


class ArchivoReemplazarView(ImagenologiaPermisoMixin, View):
    def post(self, request, pk):
        archivo = get_object_or_404(ArchivoExamenImagenologico, pk=pk)
        _validar_gestion_archivo(request.user, archivo)
        motivo = request.POST.get("motivo_anulacion", "").strip()
        nuevo_archivo = request.FILES.get("archivo_reemplazo")
        if not motivo or not nuevo_archivo:
            messages.error(request, "Debes indicar motivo y seleccionar el archivo correcto.")
            return redirect("imagenologia:detalle", pk=archivo.examen_id)

        try:
            validar_archivo_clinico(nuevo_archivo)
        except Exception:
            messages.error(request, "El archivo de reemplazo no cumple las reglas de seguridad.")
            return redirect("imagenologia:detalle", pk=archivo.examen_id)

        with transaction.atomic():
            reemplazo = _crear_archivo_examen(
                archivo.examen,
                nuevo_archivo,
                request.user,
                es_principal=archivo.es_principal,
            )
            archivo.estado = ArchivoExamenImagenologico.ESTADO_REEMPLAZADO
            archivo.motivo_anulacion = motivo
            archivo.fecha_anulacion = timezone.now()
            archivo.usuario_responsable = request.user
            archivo.adjunto_reemplazo = reemplazo
            archivo.save(update_fields=[
                "estado",
                "motivo_anulacion",
                "fecha_anulacion",
                "usuario_responsable",
                "adjunto_reemplazo",
            ])

        Bitacora.registrar(
            usuario=request.user,
            modulo="imagenologia",
            accion="reemplazo_archivo",
            tabla_afectada="imagenologia_archivos",
            id_registro_afectado=archivo.id_archivo,
            descripcion=f"Archivo {archivo.nombre_original} reemplazado por {reemplazo.nombre_original}",
            request=request,
            paciente=archivo.examen.paciente,
            cita=archivo.examen.cita,
            datos_nuevos={
                "estado": archivo.estado,
                "motivo": motivo,
                "adjunto_reemplazo": reemplazo.id_archivo,
            },
        )
        messages.success(request, "Adjunto reemplazado correctamente.")
        return redirect("imagenologia:detalle", pk=archivo.examen_id)


class ObservacionCrearView(ImagenologiaPermisoMixin, View):
    def post(self, request, pk):
        examen = get_object_or_404(ExamenImagenologico, pk=pk)
        _validar_edicion_imagenologia(request.user, examen)
        observacion_texto = request.POST.get('observacion', '').strip()
        
        if observacion_texto:
            ObservacionImagenologica.objects.create(
                examen=examen,
                usuario=request.user,
                observacion=observacion_texto
            )
            messages.success(request, "Observación agregada.")
        else:
            messages.error(request, "La observación no puede estar vacía.")
            
        return redirect("imagenologia:detalle", pk=examen.id_examen)


from .models import TipoExamenImagenologico
class TipoExamenListView(ImagenologiaPermisoMixin, ListView):
    model = TipoExamenImagenologico
    template_name = "imagenologia/tipo_examen_list.html"
    context_object_name = "tipos"

class TipoExamenCrearView(ImagenologiaPermisoMixin, View):
    template_name = "imagenologia/tipo_examen_form.html"

    def get(self, request):
        if not request.user.tiene_rol("administrador"):
            raise PermissionDenied("Solo administracion puede crear tipos de examen.")
        return render(request, self.template_name, {"accion": "Crear"})

    def post(self, request):
        if not request.user.tiene_rol("administrador"):
            raise PermissionDenied("Solo administracion puede crear tipos de examen.")
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        if nombre:
            TipoExamenImagenologico.objects.create(nombre=nombre, descripcion=descripcion)
            messages.success(request, "Tipo de examen creado.")
            return redirect("imagenologia:tipos_lista")
        messages.error(request, "El nombre es obligatorio.")
        return render(request, self.template_name, {"accion": "Crear"})

class TipoExamenEditarView(ImagenologiaPermisoMixin, View):
    template_name = "imagenologia/tipo_examen_form.html"

    def get(self, request, pk):
        if not request.user.tiene_rol("administrador"):
            raise PermissionDenied("Solo administracion puede editar tipos de examen.")
        tipo = get_object_or_404(TipoExamenImagenologico, pk=pk)
        return render(request, self.template_name, {"accion": "Editar", "tipo": tipo})

    def post(self, request, pk):
        if not request.user.tiene_rol("administrador"):
            raise PermissionDenied("Solo administracion puede editar tipos de examen.")
        tipo = get_object_or_404(TipoExamenImagenologico, pk=pk)
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        estado = request.POST.get("estado")
        if nombre:
            tipo.nombre = nombre
            tipo.descripcion = descripcion
            tipo.estado = estado
            tipo.save()
            messages.success(request, "Tipo de examen actualizado.")
            return redirect("imagenologia:tipos_lista")
        messages.error(request, "El nombre es obligatorio.")
        return render(request, self.template_name, {"accion": "Editar", "tipo": tipo})
