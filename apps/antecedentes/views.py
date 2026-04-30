"""apps/antecedentes/views.py"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from django.db import transaction

from apps.core.mixins import RolRequeridoMixin
from apps.antecedentes.models import (
    CatalogoAntecedente, RegistroAntecedentesMedicos, RegistroAntecedenteDetalle
)
from apps.pacientes.models import Paciente
from apps.auditoria.models import Bitacora


class CatalogoListView(RolRequeridoMixin, ListView):
    roles_permitidos = ["administrador", "odontologo", "director", "director_clinico"]
    template_name = "antecedentes/catalogo.html"
    context_object_name = "antecedentes"
    queryset = CatalogoAntecedente.objects.filter(estado_antecedente="activo").order_by("tipo_antecedente", "nombre")


class AntecedentesPacienteView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "odontologo", "director", "director_clinico"]
    template_name = "antecedentes/lista.html"

    def get(self, request, paciente_id):
        paciente = get_object_or_404(Paciente.objects.select_related("id_persona"), pk=paciente_id)
        registros = (
            RegistroAntecedentesMedicos.objects.filter(id_paciente=paciente)
            .select_related("id_usuario_registra__id_persona")
            .prefetch_related("detalles__id_catalogo_antecedente")
            .order_by("-fecha_registro")
        )
        return render(request, self.template_name, {
            "paciente": paciente,
            "registros": registros,
        })


class RegistrarAntecedentesView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "odontologo", "director", "director_clinico"]
    template_name = "antecedentes/registro_form.html"

    def get(self, request, paciente_id):
        paciente = get_object_or_404(Paciente.objects.select_related("id_persona"), pk=paciente_id)
        catalogo = CatalogoAntecedente.objects.filter(estado_antecedente="activo").order_by("tipo_antecedente", "nombre")
        return render(request, self.template_name, {
            "paciente": paciente,
            "catalogo": catalogo,
        })

    def post(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        observaciones = request.POST.get("observaciones_generales", "")
        antecedentes_ids = request.POST.getlist("antecedentes")

        with transaction.atomic():
            registro = RegistroAntecedentesMedicos.objects.create(
                id_paciente=paciente,
                observaciones_generales=observaciones,
                id_usuario_registra=request.user,
            )
            for ant_id in antecedentes_ids:
                try:
                    cat = CatalogoAntecedente.objects.get(pk=ant_id)
                    detalle_txt = request.POST.get(f"detalle_{ant_id}", "")
                    RegistroAntecedenteDetalle.objects.create(
                        id_registro_antecedente=registro,
                        id_catalogo_antecedente=cat,
                        detalle_adicional=detalle_txt or None,
                    )
                except CatalogoAntecedente.DoesNotExist:
                    pass

        Bitacora.registrar(
            usuario=request.user,
            modulo="antecedentes",
            accion="creacion",
            tabla_afectada="registros_antecedentes_medicos",
            id_registro_afectado=registro.id_registro_antecedente,
            descripcion=f"Antecedentes registrados para {paciente.nombre_completo}",
            ip_origen=getattr(request, "ip_origen", None),
        )
        messages.success(request, "Antecedentes médicos registrados correctamente.")
        return redirect("antecedentes:lista", paciente_id=paciente_id)


class EditarAntecedentesView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "odontologo", "director", "director_clinico"]
    """Editar un registro de antecedentes existente."""
    template_name = "antecedentes/registro_form.html"

    def get(self, request, pk):
        registro = get_object_or_404(
            RegistroAntecedentesMedicos.objects.select_related("id_paciente__id_persona")
            .prefetch_related("detalles__id_catalogo_antecedente"),
            pk=pk,
        )
        catalogo = CatalogoAntecedente.objects.filter(estado_antecedente="activo").order_by("tipo_antecedente", "nombre")
        # Marcar los antecedentes ya seleccionados
        seleccionados = {d.id_catalogo_antecedente_id: d.detalle_adicional or "" for d in registro.detalles.all()}
        return render(request, self.template_name, {
            "paciente": registro.id_paciente,
            "catalogo": catalogo,
            "registro": registro,
            "seleccionados": seleccionados,
            "editar": True,
        })

    def post(self, request, pk):
        registro = get_object_or_404(RegistroAntecedentesMedicos, pk=pk)
        observaciones = request.POST.get("observaciones_generales", "")
        antecedentes_ids = request.POST.getlist("antecedentes")

        with transaction.atomic():
            registro.observaciones_generales = observaciones
            registro.save(update_fields=["observaciones_generales"])
            # Reemplazar detalles
            RegistroAntecedenteDetalle.objects.filter(id_registro_antecedente=registro).delete()
            for ant_id in antecedentes_ids:
                try:
                    cat = CatalogoAntecedente.objects.get(pk=ant_id)
                    detalle_txt = request.POST.get(f"detalle_{ant_id}", "")
                    RegistroAntecedenteDetalle.objects.create(
                        id_registro_antecedente=registro,
                        id_catalogo_antecedente=cat,
                        detalle_adicional=detalle_txt or None,
                    )
                except CatalogoAntecedente.DoesNotExist:
                    pass

        Bitacora.registrar(
            usuario=request.user,
            modulo="antecedentes",
            accion="edicion",
            tabla_afectada="registros_antecedentes_medicos",
            id_registro_afectado=registro.id_registro_antecedente,
            descripcion=f"Antecedentes editados para {registro.id_paciente.nombre_completo}",
            ip_origen=getattr(request, "ip_origen", None),
        )
        messages.success(request, "Antecedentes médicos actualizados correctamente.")
        return redirect("antecedentes:lista", paciente_id=registro.id_paciente_id)
