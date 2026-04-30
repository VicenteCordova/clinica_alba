"""
apps/pacientes/views.py
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.http import HttpResponse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from apps.core.mixins import RolRequeridoMixin
from apps.pacientes.models import Paciente
from apps.personas.models import Persona
from apps.pacientes.forms import PersonaBaseForm, PacienteForm
from apps.fichas.models import FichaClinica
from apps.auditoria.models import Bitacora
from apps.core.permissions import puede_ver_imagenologia


class PacienteListView(RolRequeridoMixin, ListView):
    roles_permitidos = ["administrador", "administrativo", "recepcionista", "odontologo", "director", "director_clinico"]
    template_name = "pacientes/lista.html"
    context_object_name = "pacientes"
    paginate_by = 25
    queryset = (
        Paciente.objects.select_related("id_persona__id_sexo")
        .order_by("id_persona__apellido_paterno", "id_persona__nombres")
    )

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.tiene_rol("odontologo") and not self.request.user.tiene_rol(
            "administrador", "director", "director_clinico"
        ):
            qs = qs.filter(citas__id_odontologo__id_usuario=self.request.user).distinct()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                id_persona__rut__icontains=q
            ) | qs.filter(
                id_persona__nombres__icontains=q
            ) | qs.filter(
                id_persona__apellido_paterno__icontains=q
            ) | qs.filter(
                id_persona__correo__icontains=q
            ) | qs.filter(
                id_persona__telefono__icontains=q
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class PacienteCrearView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista"]
    template_name = "pacientes/crear.html"

    def get(self, request):
        return render(request, self.template_name, {
            "persona_form": PersonaBaseForm(prefix="persona"),
            "paciente_form": PacienteForm(prefix="paciente"),
        })

    def post(self, request):
        persona_form = PersonaBaseForm(data=request.POST, prefix="persona")
        paciente_form = PacienteForm(data=request.POST, prefix="paciente")

        if persona_form.is_valid() and paciente_form.is_valid():
            with transaction.atomic():
                persona = persona_form.save()
                paciente = paciente_form.save(commit=False)
                paciente.id_persona = persona
                paciente.save()

            Bitacora.registrar(
                usuario=request.user,
                modulo="pacientes",
                accion="creacion",
                tabla_afectada="pacientes",
                id_registro_afectado=paciente.id_paciente,
                descripcion=f"Paciente {persona.nombre_completo} registrado (RUT: {persona.rut})",
                ip_origen=getattr(request, "ip_origen", None),
            )
            messages.success(request, f"Paciente {persona.nombre_completo} registrado correctamente.")
            return redirect("pacientes:detalle", pk=paciente.id_paciente)

        return render(request, self.template_name, {
            "persona_form": persona_form,
            "paciente_form": paciente_form,
        })


class PacienteDetalleView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista", "odontologo", "director", "director_clinico"]
    template_name = "pacientes/detalle.html"

    def get(self, request, pk):
        from apps.agenda.models import Cita
        from apps.presupuestos.models import Presupuesto
        from apps.fichas.models import EvolucionClinica
        from apps.imagenologia.models import ExamenImagenologico
        from apps.odontograma.models import Odontograma
        from apps.tratamientos.models import PlanTratamiento
        from apps.pagos.models import Pago
        from apps.auditoria.models import Bitacora

        paciente = get_object_or_404(
            Paciente.objects.select_related("id_persona__id_sexo", "ficha_clinica")
            .prefetch_related(
                "citas__id_odontologo__id_usuario__id_persona",
                "citas__id_estado_cita", 
                "citas__id_box",
                "examenes_imagenologicos",
                "ficha_clinica__odontogramas"
            ),
            pk=pk,
        )
        if request.user.tiene_rol("odontologo") and not request.user.tiene_rol(
            "administrador", "director", "director_clinico"
        ):
            if not paciente.citas.filter(id_odontologo__id_usuario=request.user).exists():
                raise PermissionDenied("No tienes permisos para ver este paciente.")
        tiene_ficha = hasattr(paciente, 'ficha_clinica')
        
        # Calcular próxima cita
        proxima_cita = paciente.citas.filter(
            fecha_hora_inicio__gte=timezone.now(),
            id_estado_cita__nombre__in=['agendada', 'confirmada', 'en_espera']
        ).order_by('fecha_hora_inicio').first()

        ficha = getattr(paciente, "ficha_clinica", None)
        evoluciones = EvolucionClinica.objects.none()
        odontogramas = Odontograma.objects.none()
        imagenes = ExamenImagenologico.objects.none()
        planes = PlanTratamiento.objects.none()
        presupuestos = Presupuesto.objects.none()
        pagos = Pago.objects.none()
        auditoria = Bitacora.objects.none()
        deuda_total = 0

        if ficha:
            evoluciones = (
                EvolucionClinica.objects.filter(id_cita__id_paciente=paciente)
                .select_related("id_cita__id_odontologo__id_usuario__id_persona")
                .prefetch_related("adjuntos")
                .order_by("-fecha_evolucion")
            )
            odontogramas = Odontograma.objects.filter(id_ficha_clinica=ficha).order_by("-version")
            if puede_ver_imagenologia(request.user):
                imagenes = (
                    ExamenImagenologico.objects.filter(paciente=paciente)
                    .select_related("tipo_examen", "creado_por__id_persona")
                    .prefetch_related("archivos")
                    .order_by("-fecha_examen", "-id_examen")
                )
            planes = (
                PlanTratamiento.objects.filter(id_ficha_clinica=ficha)
                .select_related("id_odontologo__id_usuario__id_persona")
                .prefetch_related("detalles__id_tratamiento", "presupuestos")
                .order_by("-fecha_creacion")
            )
            presupuestos = (
                Presupuesto.objects.filter(id_plan_tratamiento__id_ficha_clinica=ficha)
                .prefetch_related("pagos")
                .order_by("-fecha_emision")
            )
            pagos = (
                Pago.objects.filter(id_presupuesto__id_plan_tratamiento__id_ficha_clinica=ficha)
                .select_related("id_medio_pago", "id_presupuesto")
                .order_by("-fecha_pago")
            )
            auditoria = Bitacora.objects.filter(paciente=paciente).select_related("id_usuario__id_persona")[:25]
            deuda_total = sum(p.saldo_pendiente for p in presupuestos if p.estado_presupuesto == "aceptado")
        
        return render(request, self.template_name, {
            "paciente": paciente,
            "tiene_ficha": tiene_ficha,
            "ficha": ficha,
            "evoluciones": evoluciones,
            "odontogramas": odontogramas,
            "imagenes": imagenes,
            "planes": planes,
            "presupuestos": presupuestos,
            "pagos": pagos,
            "auditoria": auditoria,
            "proxima_cita": proxima_cita,
            "deuda_total": deuda_total,
        })


class PacienteEditarView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista"]
    template_name = "pacientes/editar.html"

    def get(self, request, pk):
        paciente = get_object_or_404(Paciente.objects.select_related("id_persona"), pk=pk)
        return render(request, self.template_name, {
            "paciente": paciente,
            "persona_form": PersonaBaseForm(instance=paciente.id_persona, prefix="persona"),
            "paciente_form": PacienteForm(instance=paciente, prefix="paciente"),
        })

    def post(self, request, pk):
        paciente = get_object_or_404(Paciente.objects.select_related("id_persona"), pk=pk)
        persona_form = PersonaBaseForm(data=request.POST, instance=paciente.id_persona, prefix="persona")
        paciente_form = PacienteForm(data=request.POST, instance=paciente, prefix="paciente")

        if persona_form.is_valid() and paciente_form.is_valid():
            persona_form.save()
            paciente_form.save()
            Bitacora.registrar(
                usuario=request.user,
                modulo="pacientes",
                accion="edicion",
                tabla_afectada="pacientes",
                id_registro_afectado=paciente.id_paciente,
                descripcion=f"Paciente {paciente.nombre_completo} editado",
                ip_origen=getattr(request, "ip_origen", None),
            )
            messages.success(request, "Datos del paciente actualizados.")
            return redirect("pacientes:detalle", pk=pk)

        return render(request, self.template_name, {
            "paciente": paciente,
            "persona_form": persona_form,
            "paciente_form": paciente_form,
        })


class PacienteBuscarHTMXView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista", "odontologo", "director", "director_clinico"]
    """Vista HTMX para búsqueda de pacientes en el topbar."""
    template_name = "pacientes/partials/resultados_busqueda.html"

    def get(self, request):
        q = request.GET.get("q", "").strip()
        pacientes = []
        if len(q) >= 2:
            from django.db.models import Q
            query = (
                Q(id_persona__rut__icontains=q) |
                Q(id_persona__nombres__icontains=q) |
                Q(id_persona__apellido_paterno__icontains=q) |
                Q(id_persona__apellido_materno__icontains=q) |
                Q(id_persona__telefono__icontains=q) |
                Q(id_persona__correo__icontains=q) |
                Q(ficha_clinica__numero_ficha__icontains=q)
            )
            pacientes_qs = Paciente.objects.select_related("id_persona", "ficha_clinica").filter(query)
            if request.user.tiene_rol("odontologo") and not request.user.tiene_rol(
                "administrador", "director", "director_clinico"
            ):
                pacientes_qs = pacientes_qs.filter(citas__id_odontologo__id_usuario=request.user)
            pacientes = pacientes_qs.distinct()[:10]
            
        return render(request, self.template_name, {"pacientes": pacientes, "q": q})
