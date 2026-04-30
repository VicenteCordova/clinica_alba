"""apps/odontologos/views.py"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from django.db import transaction

from apps.core.mixins import RolRequeridoMixin
from apps.odontologos.models import Odontologo, Especialidad, HorarioOdontologo
from apps.odontologos.forms import OdontologoForm
from apps.auditoria.models import Bitacora


class OdontologoListView(RolRequeridoMixin, ListView):
    roles_permitidos = ["administrador", "administrativo", "recepcionista", "odontologo", "director", "director_clinico"]
    template_name = "odontologos/lista.html"
    context_object_name = "odontologos"
    paginate_by = 20
    queryset = (
        Odontologo.objects.select_related("id_usuario__id_persona")
        .prefetch_related("odontologo_especialidades__especialidad")
        .order_by("id_usuario__id_persona__apellido_paterno")
    )


class OdontologoDetalleView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista", "odontologo", "director", "director_clinico"]
    template_name = "odontologos/detalle.html"

    def get(self, request, pk):
        odontologo = get_object_or_404(
            Odontologo.objects.select_related("id_usuario__id_persona")
            .prefetch_related("odontologo_especialidades__especialidad", "horarios"),
            pk=pk,
        )
        return render(request, self.template_name, {"odontologo": odontologo})


class OdontologoCrearView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador"]
    template_name = "odontologos/crear.html"

    def get(self, request):
        form = OdontologoForm()
        from apps.accounts.models import Usuario
        usuarios_disponibles = Usuario.objects.filter(
            estado_acceso="activo"
        ).exclude(
            odontologo__isnull=False
        ).select_related("id_persona")
        return render(request, self.template_name, {
            "form": form,
            "usuarios_disponibles": usuarios_disponibles,
        })

    def post(self, request):
        form = OdontologoForm(data=request.POST)
        if form.is_valid():
            usuario_id = request.POST.get("id_usuario")
            if not usuario_id:
                messages.error(request, "Debes seleccionar un usuario para el odontólogo.")
                from apps.accounts.models import Usuario
                usuarios_disponibles = Usuario.objects.filter(
                    estado_acceso="activo"
                ).exclude(odontologo__isnull=False).select_related("id_persona")
                return render(request, self.template_name, {
                    "form": form,
                    "usuarios_disponibles": usuarios_disponibles,
                })
            from apps.accounts.models import Usuario
            usuario = get_object_or_404(Usuario, pk=usuario_id)
            with transaction.atomic():
                odontologo = form.save(commit=False)
                odontologo.id_usuario = usuario
                odontologo.save()
                form.save_especialidades(odontologo)

            Bitacora.registrar(
                usuario=request.user,
                modulo="odontologos",
                accion="creacion",
                tabla_afectada="odontologos",
                id_registro_afectado=odontologo.id_odontologo,
                descripcion=f"Odontólogo {odontologo.nombre_completo} registrado",
                ip_origen=getattr(request, "ip_origen", None),
            )
            messages.success(request, f"Odontólogo {odontologo.nombre_completo} registrado correctamente.")
            return redirect("odontologos:detalle", pk=odontologo.id_odontologo)

        from apps.accounts.models import Usuario
        usuarios_disponibles = Usuario.objects.filter(
            estado_acceso="activo"
        ).exclude(odontologo__isnull=False).select_related("id_persona")
        return render(request, self.template_name, {
            "form": form,
            "usuarios_disponibles": usuarios_disponibles,
        })


class OdontologoEditarView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador"]
    template_name = "odontologos/editar.html"

    def get(self, request, pk):
        odontologo = get_object_or_404(Odontologo.objects.select_related("id_usuario__id_persona"), pk=pk)
        form = OdontologoForm(instance=odontologo)
        return render(request, self.template_name, {
            "odontologo": odontologo,
            "form": form,
        })

    def post(self, request, pk):
        odontologo = get_object_or_404(Odontologo, pk=pk)
        form = OdontologoForm(data=request.POST, instance=odontologo)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                form.save_especialidades(odontologo)
            Bitacora.registrar(
                usuario=request.user,
                modulo="odontologos",
                accion="edicion",
                tabla_afectada="odontologos",
                id_registro_afectado=odontologo.id_odontologo,
                descripcion=f"Odontólogo {odontologo.nombre_completo} editado",
                ip_origen=getattr(request, "ip_origen", None),
            )
            messages.success(request, "Datos del odontólogo actualizados correctamente.")
            return redirect("odontologos:detalle", pk=pk)
        return render(request, self.template_name, {
            "odontologo": odontologo,
            "form": form,
        })
