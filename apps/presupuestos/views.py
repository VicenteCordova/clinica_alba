"""apps/presupuestos/views.py"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import PermissionDenied

from apps.core.mixins import RolRequeridoMixin
from apps.presupuestos.models import Presupuesto, PresupuestoDetalle
from apps.tratamientos.models import PlanTratamiento, PlanTratamientoDetalle
from apps.core.utils import generar_numero_correlativo
from apps.auditoria.models import Bitacora


class PresupuestoListView(RolRequeridoMixin, ListView):
    roles_permitidos = ["administrador", "administrativo", "recepcionista", "cajero", "odontologo", "director", "director_clinico"]
    template_name = "presupuestos/lista.html"
    context_object_name = "presupuestos"
    paginate_by = 20
    queryset = (
        Presupuesto.objects.select_related(
            "id_plan_tratamiento__id_ficha_clinica__id_paciente__id_persona",
            "id_plan_tratamiento__id_odontologo__id_usuario",
            "id_usuario_emite__id_persona",
        ).order_by("-fecha_emision")
    )

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.tiene_rol("odontologo") and not self.request.user.tiene_rol(
            "administrador", "director", "director_clinico"
        ):
            qs = qs.filter(id_plan_tratamiento__id_odontologo__id_usuario=self.request.user)
        return qs


class PresupuestoDetalleView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista", "cajero", "odontologo", "director", "director_clinico"]
    template_name = "presupuestos/detalle.html"

    def get(self, request, pk):
        presupuesto = get_object_or_404(
            Presupuesto.objects.select_related(
                "id_plan_tratamiento__id_ficha_clinica__id_paciente__id_persona",
                "id_plan_tratamiento__id_odontologo__id_usuario",
            ).prefetch_related("detalles", "pagos__id_medio_pago"),
            pk=pk,
        )
        if request.user.tiene_rol("odontologo") and not request.user.tiene_rol(
            "administrador", "director", "director_clinico"
        ):
            if presupuesto.id_plan_tratamiento.id_odontologo.id_usuario_id != request.user.id_usuario:
                raise PermissionDenied("No tienes permisos para ver este presupuesto.")
        return render(request, self.template_name, {
            "presupuesto": presupuesto,
            "pagos": presupuesto.pagos.order_by("-fecha_pago"),
        })


class PresupuestoEmitirView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista", "cajero"]
    """Emite un presupuesto desde un plan de tratamiento."""
    template_name = "presupuestos/emitir_form.html"

    def get(self, request, plan_id):
        plan = get_object_or_404(
            PlanTratamiento.objects.prefetch_related(
                "detalles__id_tratamiento"
            ),
            pk=plan_id,
        )
        detalles_pendientes = plan.detalles.filter(
            estado_detalle__in=["pendiente", "aprobado"]
        )
        ya_presupuestados = PresupuestoDetalle.objects.filter(
            id_presupuesto__id_plan_tratamiento=plan,
            id_presupuesto__estado_presupuesto__in=["vigente", "aceptado"],
        ).values_list("id_plan_detalle_id", flat=True)
        detalles_pendientes = detalles_pendientes.exclude(id_plan_detalle__in=ya_presupuestados)
        return render(request, self.template_name, {
            "plan": plan,
            "detalles": detalles_pendientes,
        })

    def post(self, request, plan_id):
        plan = get_object_or_404(PlanTratamiento, pk=plan_id)
        if not request.user.tiene_rol("administrador", "director", "director_clinico"):
            descuento = 0.0
            messages.info(request, "No tienes permisos para aplicar descuentos. Se ha forzado a 0.")
        else:
            descuento = request.POST.get("descuento_total", "0") or "0"
            try:
                descuento = float(descuento)
            except ValueError:
                descuento = 0.0

        with transaction.atomic():
            # Calcular monto_bruto desde detalles seleccionados
            detalles_ids = request.POST.getlist("detalles")
            detalles = PlanTratamientoDetalle.objects.filter(
                id_plan_detalle__in=detalles_ids,
                id_plan_tratamiento=plan,
            )
            if not detalles.exists():
                messages.error(request, "Debes seleccionar al menos un ítem del plan.")
                return redirect("presupuestos:emitir", plan_id=plan_id)

            duplicados = PresupuestoDetalle.objects.filter(
                id_plan_detalle__in=detalles,
                id_presupuesto__estado_presupuesto__in=["vigente", "aceptado"],
            )
            if duplicados.exists():
                messages.warning(
                    request,
                    "Uno o mas items seleccionados ya pertenecen a un presupuesto activo."
                )
                return redirect("presupuestos:emitir", plan_id=plan_id)

            monto_bruto = sum(d.subtotal for d in detalles)
            monto_final = monto_bruto - descuento

            if monto_final < 0:
                messages.error(request, "El descuento no puede superar el monto bruto.")
                return redirect("presupuestos:emitir", plan_id=plan_id)

            numero = generar_numero_correlativo(Presupuesto, "numero_presupuesto", "PRES", 6)
            presupuesto = Presupuesto.objects.create(
                id_plan_tratamiento=plan,
                numero_presupuesto=numero,
                monto_bruto=monto_bruto,
                descuento_total=descuento,
                monto_final=monto_final,
                id_usuario_emite=request.user,
            )
            for detalle in detalles:
                PresupuestoDetalle.objects.create(
                    id_presupuesto=presupuesto,
                    id_plan_detalle=detalle,
                    descripcion_item=detalle.id_tratamiento.nombre,
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.valor_unitario,
                    subtotal=detalle.subtotal,
                )

        Bitacora.registrar(
            usuario=request.user,
            modulo="presupuestos",
            accion="emision",
            tabla_afectada="presupuestos",
            id_registro_afectado=presupuesto.id_presupuesto,
            descripcion=f"Presupuesto {numero} emitido por ${monto_final:,.0f}",
            ip_origen=getattr(request, "ip_origen", None),
        )
        messages.success(request, f"Presupuesto {numero} emitido correctamente.")
        return redirect("presupuestos:detalle", pk=presupuesto.id_presupuesto)


class PresupuestoCambiarEstadoView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista", "cajero"]
    """Cambiar estado del presupuesto con validación de transiciones de negocio."""

    TRANSICIONES_VALIDAS = {
        "vigente": ["aceptado", "rechazado", "anulado", "vencido"],
        "aceptado": ["anulado"],
        "pagado_parcial": ["anulado"],
        "pagado_total": [],
        "vencido": ["vigente", "anulado"],
        "rechazado": ["anulado"],
        "anulado": [],  # Estado final
    }

    def post(self, request, pk):
        if not request.user.tiene_rol("cajero", "administrativo", "recepcionista", "administrador"):
            raise PermissionDenied("No tienes permisos para cambiar estados de presupuestos.")
        presupuesto = get_object_or_404(Presupuesto, pk=pk)
        nuevo_estado = request.POST.get("estado", "").strip()

        if nuevo_estado not in dict(Presupuesto.ESTADO_CHOICES):
            messages.error(request, "Estado inválido.")
            return redirect("presupuestos:detalle", pk=pk)

        transiciones = self.TRANSICIONES_VALIDAS.get(presupuesto.estado_presupuesto, [])
        if nuevo_estado not in transiciones:
            messages.error(
                request,
                f"No se puede cambiar de '{presupuesto.estado_presupuesto}' a '{nuevo_estado}'."
            )
            return redirect("presupuestos:detalle", pk=pk)

        # Validar que no se anule un presupuesto con pagos vigentes
        if nuevo_estado == "anulado":
            pagos_vigentes = presupuesto.pagos.filter(estado_pago="vigente").count()
            if pagos_vigentes > 0:
                messages.error(
                    request,
                    f"No se puede anular: el presupuesto tiene {pagos_vigentes} pago(s) vigente(s). "
                    f"Anule los pagos primero."
                )
                return redirect("presupuestos:detalle", pk=pk)

        estado_anterior = presupuesto.estado_presupuesto
        if nuevo_estado == "anulado":
            motivo = request.POST.get("motivo", "").strip()
            if not motivo:
                messages.error(request, "Debe ingresar un motivo para anular el presupuesto.")
                return redirect("presupuestos:detalle", pk=pk)
            presupuesto.motivo_anulacion = motivo
            from django.utils import timezone
            presupuesto.fecha_anulacion = timezone.now()
            presupuesto.id_usuario_anula = request.user
            presupuesto.estado_presupuesto = nuevo_estado
            presupuesto.save(update_fields=["estado_presupuesto", "motivo_anulacion", "fecha_anulacion", "id_usuario_anula"])
        else:
            presupuesto.estado_presupuesto = nuevo_estado
            presupuesto.save(update_fields=["estado_presupuesto"])

        Bitacora.registrar(
            usuario=request.user,
            modulo="presupuestos",
            accion="cambio_estado",
            tabla_afectada="presupuestos",
            id_registro_afectado=presupuesto.id_presupuesto,
            descripcion=f"Presupuesto {presupuesto.numero_presupuesto}: {estado_anterior} → {nuevo_estado}",
            ip_origen=getattr(request, "ip_origen", None),
        )
        messages.success(request, f"Presupuesto marcado como '{nuevo_estado}'.")
        return redirect("presupuestos:detalle", pk=pk)


class PresupuestoImprimirView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista", "cajero", "odontologo", "director", "director_clinico"]
    template_name = "presupuestos/imprimir.html"

    def get(self, request, pk):
        presupuesto = get_object_or_404(
            Presupuesto.objects.select_related(
                "id_plan_tratamiento__id_ficha_clinica__id_paciente__id_persona",
                "id_plan_tratamiento__id_odontologo__id_usuario",
                "id_usuario_emite__id_persona",
            ).prefetch_related("detalles"),
            pk=pk,
        )
        if request.user.tiene_rol("odontologo") and not request.user.tiene_rol(
            "administrador", "director", "director_clinico"
        ):
            if presupuesto.id_plan_tratamiento.id_odontologo.id_usuario_id != request.user.id_usuario:
                raise PermissionDenied("No tienes permisos para imprimir este presupuesto.")
        return render(request, self.template_name, {
            "presupuesto": presupuesto,
        })
