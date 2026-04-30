"""
apps/agenda/views.py
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views import View
from django.db import DatabaseError
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied

from apps.core.mixins import RolRequeridoMixin
from apps.agenda.models import Cita, EstadoCita, Box, TipoAtencion
from apps.agenda.forms import CitaForm, CambiarEstadoCitaForm
from apps.agenda.services import CitaService
from apps.auditoria.models import Bitacora


class CalendarioView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista", "odontologo", "director", "director_clinico"]
    template_name = "agenda/calendario.html"

    def get(self, request):
        boxes = Box.objects.filter(estado_box="activo")
        from apps.odontologos.models import Odontologo
        odontologos = Odontologo.objects.filter(
            estado_profesional="activo"
        ).select_related("id_usuario__id_persona")
        estados = EstadoCita.objects.all()
        return render(request, self.template_name, {
            "boxes": boxes,
            "odontologos": odontologos,
            "estados": estados,
        })


class CitasJsonView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista", "odontologo", "director", "director_clinico"]
    """Endpoint JSON para FullCalendar."""

    def get(self, request):
        qs = Cita.objects.select_related(
            "id_paciente__id_persona",
            "id_odontologo__id_usuario__id_persona",
            "id_estado_cita",
            "id_box",
        )
        if request.user.tiene_rol("odontologo") and not request.user.tiene_rol(
            "administrador", "administrativo", "recepcionista", "director", "director_clinico"
        ):
            qs = qs.filter(id_odontologo__id_usuario=request.user)
        # Filtros opcionales
        od = request.GET.get("odontologo")
        box = request.GET.get("box")
        estado = request.GET.get("estado")
        if od:
            qs = qs.filter(id_odontologo_id=od)
        if box:
            qs = qs.filter(id_box_id=box)
        if estado:
            qs = qs.filter(id_estado_cita__nombre=estado)

        # Colores por estado
        COLORES = {
            "pendiente": "#f59e0b",
            "confirmada": "#7c88ff",
            "atendida": "#10b981",
            "cancelada": "#ef4444",
            "reprogramada": "#94a3b8",
        }

        eventos = []
        for c in qs:
            estado_nombre = c.id_estado_cita.nombre
            eventos.append({
                "id": c.id_cita,
                "title": (
                    f"{c.id_paciente.nombre_completo} "
                    f"— Dr(a). {c.id_odontologo.nombre_completo}"
                ),
                "start": c.fecha_hora_inicio.isoformat(),
                "end": c.fecha_hora_fin.isoformat(),
                "backgroundColor": COLORES.get(estado_nombre, "#7c88ff"),
                "borderColor": COLORES.get(estado_nombre, "#7c88ff"),
                "extendedProps": {
                    "estado": estado_nombre,
                    "box": c.id_box.nombre,
                    "paciente_id": c.id_paciente_id,
                    "url": f"/agenda/citas/{c.id_cita}/",
                },
            })
        return JsonResponse(eventos, safe=False)


class CitaCrearView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista"]
    template_name = "agenda/cita_form.html"

    def get(self, request):
        form = CitaForm()
        return render(request, self.template_name, {"form": form, "titulo": "Nueva Cita"})

    def post(self, request):
        form = CitaForm(data=request.POST)
        if form.is_valid():
            try:
                cita = CitaService.crear_cita(
                    datos=form.cleaned_data, usuario=request.user
                )
                messages.success(
                    request,
                    f"Cita agendada correctamente para {cita.fecha_hora_inicio:%d/%m/%Y %H:%M}.",
                )
                return redirect("agenda:calendario")
            except (ValidationError, DatabaseError) as e:
                messages.error(request, str(e).strip("[]'\""))
        return render(request, self.template_name, {"form": form, "titulo": "Nueva Cita"})


class CitaDetalleView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista", "odontologo", "director", "director_clinico"]
    template_name = "agenda/cita_detalle.html"

    def get(self, request, pk):
        cita = get_object_or_404(
            Cita.objects.select_related(
                "id_paciente__id_persona",
                "id_odontologo__id_usuario__id_persona",
                "id_estado_cita",
                "id_box",
                "id_tipo_atencion",
                "id_usuario_registra",
            ).prefetch_related("historial__id_estado_nuevo", "historial__id_estado_anterior"),
            pk=pk,
        )
        if request.user.tiene_rol("odontologo") and not request.user.tiene_rol(
            "administrador", "administrativo", "recepcionista", "director", "director_clinico"
        ):
            if cita.id_odontologo.id_usuario_id != request.user.id_usuario:
                raise PermissionDenied("No tienes permisos para ver esta cita.")
        cambiar_form = CambiarEstadoCitaForm()
        return render(request, self.template_name, {
            "cita": cita,
            "cambiar_form": cambiar_form,
        })


class CitaEditarView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista"]
    template_name = "agenda/cita_form.html"

    def get(self, request, pk):
        cita = get_object_or_404(Cita, pk=pk)
        form = CitaForm(instance=cita)
        return render(request, self.template_name, {"form": form, "titulo": "Editar Cita", "cita": cita})

    def post(self, request, pk):
        cita = get_object_or_404(Cita, pk=pk)
        form = CitaForm(data=request.POST, instance=cita)
        if form.is_valid():
            try:
                CitaService.editar_cita(
                    cita=cita, datos=form.cleaned_data, usuario=request.user
                )
                messages.success(request, "Cita actualizada correctamente.")
                return redirect("agenda:detalle_cita", pk=pk)
            except (ValidationError, DatabaseError) as e:
                messages.error(request, str(e).strip("[]'\""))
        return render(request, self.template_name, {"form": form, "titulo": "Editar Cita", "cita": cita})


class CitaCambiarEstadoView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista"]
    def post(self, request, pk):
        cita = get_object_or_404(Cita, pk=pk)
        form = CambiarEstadoCitaForm(data=request.POST)
        if form.is_valid():
            try:
                CitaService.cambiar_estado(
                    cita=cita,
                    nuevo_estado=form.cleaned_data["nuevo_estado"],
                    usuario=request.user,
                    motivo=form.cleaned_data.get("motivo_cambio"),
                )
                messages.success(
                    request,
                    f"Estado de la cita actualizado a '{form.cleaned_data['nuevo_estado'].nombre}'.",
                )
            except ValidationError as e:
                messages.error(request, str(e))
        return redirect("agenda:detalle_cita", pk=pk)

class CitaCambiarEstadoHTMXView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista"]
    """Vista HTMX para botones de acción rápida en dashboards."""
    def post(self, request, pk, nuevo_estado):
        cita = get_object_or_404(Cita, pk=pk)
        try:
            estado_obj = get_object_or_404(EstadoCita, nombre=nuevo_estado)
            CitaService.cambiar_estado(
                cita=cita,
                nuevo_estado=estado_obj,
                usuario=request.user,
                motivo="Cambio rápido desde dashboard"
            )
            from django.http import HttpResponse
            response = HttpResponse(f'<span class="badge-estado {estado_obj.nombre}">{estado_obj.nombre}</span>')
            response['HX-Trigger'] = 'estadoCitaCambiado'
            return response
        except Exception as e:
            from django.http import HttpResponse
            return HttpResponse(f'<span class="text-danger small">{str(e)}</span>', status=400)
