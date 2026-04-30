"""apps/tratamientos/views.py"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from apps.core.mixins import RolRequeridoMixin
from apps.tratamientos.models import Tratamiento, PlanTratamiento, PlanTratamientoDetalle
from apps.tratamientos.forms import TratamientoForm
from apps.fichas.models import FichaClinica
from apps.auditoria.models import Bitacora


class TratamientoListView(RolRequeridoMixin, ListView):
    roles_permitidos = ["administrador", "odontologo", "director", "director_clinico"]
    template_name = "tratamientos/catalogo.html"
    context_object_name = "tratamientos"
    queryset = Tratamiento.objects.filter(estado_tratamiento="activo").order_by("nombre")


class TratamientoCrearView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador"]
    template_name = "tratamientos/tratamiento_form.html"

    def get(self, request):
        form = TratamientoForm()
        return render(request, self.template_name, {"form": form, "titulo": "Nuevo tratamiento"})

    def post(self, request):
        form = TratamientoForm(data=request.POST)
        if form.is_valid():
            tratamiento = form.save()
            Bitacora.registrar(
                usuario=request.user,
                modulo="tratamientos",
                accion="creacion",
                tabla_afectada="tratamientos",
                id_registro_afectado=tratamiento.id_tratamiento,
                descripcion=f"Tratamiento [{tratamiento.codigo}] {tratamiento.nombre} creado",
                ip_origen=getattr(request, "ip_origen", None),
            )
            messages.success(request, f"Tratamiento «{tratamiento.nombre}» creado correctamente.")
            return redirect("tratamientos:lista")
        return render(request, self.template_name, {"form": form, "titulo": "Nuevo tratamiento"})


class TratamientoEditarView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador"]
    template_name = "tratamientos/tratamiento_form.html"

    def get(self, request, pk):
        tratamiento = get_object_or_404(Tratamiento, pk=pk)
        form = TratamientoForm(instance=tratamiento)
        return render(request, self.template_name, {
            "form": form,
            "tratamiento": tratamiento,
            "titulo": f"Editar {tratamiento.nombre}",
        })

    def post(self, request, pk):
        tratamiento = get_object_or_404(Tratamiento, pk=pk)
        form = TratamientoForm(data=request.POST, instance=tratamiento)
        if form.is_valid():
            form.save()
            Bitacora.registrar(
                usuario=request.user,
                modulo="tratamientos",
                accion="edicion",
                tabla_afectada="tratamientos",
                id_registro_afectado=tratamiento.id_tratamiento,
                descripcion=f"Tratamiento [{tratamiento.codigo}] {tratamiento.nombre} editado",
                ip_origen=getattr(request, "ip_origen", None),
            )
            messages.success(request, "Tratamiento actualizado correctamente.")
            return redirect("tratamientos:lista")
        return render(request, self.template_name, {
            "form": form,
            "tratamiento": tratamiento,
            "titulo": f"Editar {tratamiento.nombre}",
        })


class PlanTratamientoListView(RolRequeridoMixin, ListView):
    roles_permitidos = ["administrador", "odontologo", "director", "director_clinico", "recepcionista", "administrativo"]
    template_name = "tratamientos/plan_lista.html"
    context_object_name = "planes"
    paginate_by = 20
    queryset = (
        PlanTratamiento.objects.select_related(
            "id_ficha_clinica__id_paciente__id_persona",
            "id_odontologo__id_usuario__id_persona",
        )
        .order_by("-fecha_creacion")
    )

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.tiene_rol("odontologo") and not self.request.user.tiene_rol(
            "administrador", "director", "director_clinico"
        ):
            qs = qs.filter(id_odontologo__id_usuario=self.request.user)
        return qs


class PlanTratamientoDetalleView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "odontologo", "director", "director_clinico", "recepcionista", "administrativo"]
    template_name = "tratamientos/plan_detalle.html"

    def get(self, request, pk):
        plan = get_object_or_404(
            PlanTratamiento.objects.select_related(
                "id_ficha_clinica__id_paciente__id_persona",
                "id_odontologo__id_usuario__id_persona",
            ).prefetch_related("detalles__id_tratamiento", "detalles__codigo_pieza_dental"),
            pk=pk,
        )
        if request.user.tiene_rol("odontologo") and not request.user.tiene_rol(
            "administrador", "director", "director_clinico"
        ):
            if plan.id_odontologo.id_usuario_id != request.user.id_usuario:
                raise PermissionDenied("No tienes permisos para ver este plan.")
        return render(request, self.template_name, {"plan": plan})


class PlanTratamientoCrearView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "odontologo", "director", "director_clinico"]
    template_name = "tratamientos/plan_form.html"

    def get(self, request, ficha_id):
        ficha = get_object_or_404(FichaClinica, pk=ficha_id)
        from apps.odontologos.models import Odontologo
        tratamientos = Tratamiento.objects.filter(estado_tratamiento="activo")
        odontologos = Odontologo.objects.filter(estado_profesional="activo").select_related(
            "id_usuario__id_persona"
        )
        odontologo_actual = odontologos.filter(id_usuario=request.user).first()
        return render(request, self.template_name, {
            "ficha": ficha,
            "tratamientos": tratamientos,
            "odontologos": odontologos,
            "odontologo_actual": odontologo_actual,
            "cita_id": request.GET.get("cita", ""),
            "evolucion_id": request.GET.get("evolucion", ""),
            "odontograma_id": request.GET.get("odontograma", ""),
        })

    def post(self, request, ficha_id):
        ficha = get_object_or_404(FichaClinica, pk=ficha_id)
        from apps.odontologos.models import Odontologo
        from apps.odontograma.models import PiezaDental
        from django.db import transaction

        odontologo_id = request.POST.get("odontologo")
        if request.user.tiene_rol("odontologo") and not request.user.tiene_rol(
            "administrador", "director", "director_clinico"
        ):
            odontologo = getattr(request.user, "odontologo", None)
            if odontologo is None:
                raise PermissionDenied("Tu usuario no tiene perfil de odontologo asociado.")
        else:
            odontologo = get_object_or_404(Odontologo, pk=odontologo_id)

        tratamiento_ids = request.POST.getlist("tratamiento_id[]")
        cantidades = request.POST.getlist("cantidad[]")
        valores = request.POST.getlist("valor_unitario[]")
        piezas = request.POST.getlist("pieza_dental[]")
        prioridades = request.POST.getlist("prioridad[]")
        observaciones_items = request.POST.getlist("observacion_item[]")
        estados_items = request.POST.getlist("estado_detalle[]")

        if not tratamiento_ids:
            messages.error(request, "Debes agregar al menos un ítem al plan.")
            return redirect("tratamientos:plan_crear", ficha_id=ficha_id)

        with transaction.atomic():
            plan = PlanTratamiento.objects.create(
                id_ficha_clinica=ficha,
                id_odontologo=odontologo,
                id_cita_id=request.POST.get("cita_id") or None,
                id_evolucion_id=request.POST.get("evolucion_id") or None,
                id_odontograma_id=request.POST.get("odontograma_id") or None,
                observaciones=request.POST.get("observaciones", ""),
            )
            for i, trat_id in enumerate(tratamiento_ids):
                if not trat_id:
                    continue
                trat = Tratamiento.objects.filter(pk=trat_id).first()
                if not trat:
                    continue
                cant = max(1, int(cantidades[i]) if cantidades[i].isdigit() else 1)
                try:
                    valor = float(valores[i]) if i < len(valores) and valores[i] else float(trat.valor_referencial)
                except ValueError:
                    valor = float(trat.valor_referencial)
                pieza_cod = piezas[i].strip() if i < len(piezas) else ""
                pieza = PiezaDental.objects.filter(codigo_pieza_dental=pieza_cod).first() if pieza_cod else None
                prioridad = None
                if i < len(prioridades) and prioridades[i].isdigit():
                    prioridad = int(prioridades[i])
                estado_detalle = estados_items[i] if i < len(estados_items) and estados_items[i] else PlanTratamientoDetalle.ESTADO_PENDIENTE
                PlanTratamientoDetalle.objects.create(
                    id_plan_tratamiento=plan,
                    id_tratamiento=trat,
                    cantidad=cant,
                    valor_unitario=valor,
                    codigo_pieza_dental=pieza,
                    nivel_prioridad=prioridad,
                    observaciones=observaciones_items[i].strip() if i < len(observaciones_items) else "",
                    estado_detalle=estado_detalle,
                )

        Bitacora.registrar(
            usuario=request.user,
            modulo="tratamientos",
            accion="creacion",
            tabla_afectada="planes_tratamiento",
            id_registro_afectado=plan.id_plan_tratamiento,
            descripcion=f"Plan #{plan.id_plan_tratamiento} creado con {len(tratamiento_ids)} ítem(s)",
            ip_origen=getattr(request, "ip_origen", None),
        )
        messages.success(request, "Plan de tratamiento creado correctamente.")
        return redirect("tratamientos:plan_detalle", pk=plan.id_plan_tratamiento)


class PlanCambiarEstadoView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "odontologo", "director", "director_clinico"]
    """Cambiar estado del plan de tratamiento con validación de transiciones."""

    TRANSICIONES_VALIDAS = {
        "activo": ["cerrado", "anulado", "propuesto", "en_curso", "finalizado"],
        "borrador": ["propuesto", "anulado"],
        "propuesto": ["aceptado", "aceptado_parcial", "rechazado", "anulado"],
        "aceptado_parcial": ["aceptado", "en_curso", "rechazado", "anulado"],
        "aceptado": ["en_curso", "finalizado", "anulado"],
        "rechazado": ["anulado"],
        "en_curso": ["finalizado", "suspendido", "anulado"],
        "finalizado": [],
        "cerrado": ["activo"],
        "anulado": [],  # Anulado es estado final
    }

    def post(self, request, pk):
        plan = get_object_or_404(PlanTratamiento, pk=pk)
        nuevo_estado = request.POST.get("estado", "").strip()

        estados_validos = dict(PlanTratamiento.ESTADO_CHOICES)
        if nuevo_estado not in estados_validos:
            messages.error(request, "Estado inválido.")
            return redirect("tratamientos:plan_detalle", pk=pk)

        transiciones = self.TRANSICIONES_VALIDAS.get(plan.estado_plan, [])
        if nuevo_estado not in transiciones:
            messages.error(
                request,
                f"No se puede cambiar de '{plan.estado_plan}' a '{nuevo_estado}'."
            )
            return redirect("tratamientos:plan_detalle", pk=pk)

        estado_anterior = plan.estado_plan
        if nuevo_estado == "anulado":
            motivo = request.POST.get("motivo", "").strip()
            if not motivo:
                messages.error(request, "Debe ingresar un motivo para anular el plan.")
                return redirect("tratamientos:plan_detalle", pk=pk)
            plan.motivo_anulacion = motivo
            from django.utils import timezone
            plan.fecha_anulacion = timezone.now()
            plan.id_usuario_anula = request.user
            plan.estado_plan = nuevo_estado
            plan.save(update_fields=["estado_plan", "motivo_anulacion", "fecha_anulacion", "id_usuario_anula"])
        else:
            plan.estado_plan = nuevo_estado
            plan.save(update_fields=["estado_plan"])
        Bitacora.registrar(
            usuario=request.user,
            modulo="tratamientos",
            accion="cambio_estado",
            tabla_afectada="planes_tratamiento",
            id_registro_afectado=plan.id_plan_tratamiento,
            descripcion=f"Plan #{plan.id_plan_tratamiento}: {estado_anterior} → {nuevo_estado}",
            ip_origen=getattr(request, "ip_origen", None),
        )
        messages.success(request, f"Plan marcado como «{nuevo_estado}».")
        return redirect("tratamientos:plan_detalle", pk=pk)
