"""
apps/pagos/views.py
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone

from apps.core.mixins import LoginRequeridoMixin, RolRequeridoMixin
from apps.presupuestos.models import Presupuesto
from apps.pagos.services import PagoService
from apps.pagos.models import Pago, MedioPago
from apps.pagos.forms import PagoForm
from apps.auditoria.models import Bitacora


class PagoListaView(RolRequeridoMixin, View):
    """Lista/historial general de pagos con filtros."""
    roles_permitidos = ["cajero", "administrativo", "recepcionista", "administrador", "director", "director_clinico"]
    template_name = "pagos/pago_lista.html"

    def get(self, request):
        from decimal import Decimal

        qs = Pago.objects.select_related(
            "id_presupuesto__id_plan_tratamiento__id_ficha_clinica__id_paciente__id_persona",
            "id_medio_pago",
            "id_usuario_registra__id_persona",
        ).order_by("-fecha_pago")

        # Filtros
        estado = request.GET.get("estado", "")
        medio = request.GET.get("medio", "")
        fecha_desde = request.GET.get("fecha_desde", "")
        fecha_hasta = request.GET.get("fecha_hasta", "")
        q = request.GET.get("q", "").strip()

        if estado:
            qs = qs.filter(estado_pago=estado)
        if medio:
            qs = qs.filter(id_medio_pago_id=medio)
        if fecha_desde:
            qs = qs.filter(fecha_pago__date__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_pago__date__lte=fecha_hasta)
        if q:
            qs = qs.filter(
                Q(id_presupuesto__numero_presupuesto__icontains=q) |
                Q(id_presupuesto__id_plan_tratamiento__id_ficha_clinica__id_paciente__id_persona__nombres__icontains=q) |
                Q(id_presupuesto__id_plan_tratamiento__id_ficha_clinica__id_paciente__id_persona__apellido_paterno__icontains=q) |
                Q(numero_comprobante__icontains=q)
            )

        # KPIs del dia
        hoy = timezone.localdate()
        pagos_hoy = Pago.objects.filter(fecha_pago__date=hoy, estado_pago="vigente")
        total_hoy = pagos_hoy.aggregate(t=Sum("monto"))["t"] or 0
        count_hoy = pagos_hoy.count()
        total_vigente = Pago.objects.filter(estado_pago="vigente").aggregate(t=Sum("monto"))["t"] or 0

        medios = MedioPago.objects.filter(estado_medio_pago="activo")

        ctx = {
            "pagos": qs,
            "medios": medios,
            "total_hoy": total_hoy,
            "count_hoy": count_hoy,
            "total_vigente": total_vigente,
            # filtros activos para repintar el form
            "filtro_estado": estado,
            "filtro_medio": medio,
            "filtro_fecha_desde": fecha_desde,
            "filtro_fecha_hasta": fecha_hasta,
            "filtro_q": q,
        }
        return render(request, self.template_name, ctx)


class PagoCrearView(RolRequeridoMixin, View):
    roles_permitidos = ["cajero", "administrativo", "recepcionista", "administrador"]
    template_name = "pagos/pago_form.html"

    def get(self, request, presupuesto_id):
        presupuesto = get_object_or_404(Presupuesto, pk=presupuesto_id)
        from apps.caja.models import Caja
        caja_abierta = Caja.objects.filter(id_usuario_apertura=request.user, estado_caja="abierta").first()
        requiere_caja = request.user.tiene_rol("cajero") and not request.user.tiene_rol("administrador", "administrativo")
        if requiere_caja and not caja_abierta:
            messages.warning(request, "Debes abrir caja antes de registrar pagos.")
            return redirect("caja:abrir")
        return render(request, self.template_name, {
            "form": PagoForm(),
            "presupuesto": presupuesto,
            "caja_abierta": caja_abierta,
        })

    def post(self, request, presupuesto_id):
        presupuesto = get_object_or_404(Presupuesto, pk=presupuesto_id)
        from apps.caja.models import Caja
        caja_abierta = Caja.objects.filter(id_usuario_apertura=request.user, estado_caja="abierta").first()
        requiere_caja = request.user.tiene_rol("cajero") and not request.user.tiene_rol("administrador", "administrativo")
        if requiere_caja and not caja_abierta:
            messages.warning(request, "Debes abrir caja antes de registrar pagos.")
            return redirect("caja:abrir")
        form = PagoForm(data=request.POST)
        if form.is_valid():
            try:
                pago = PagoService.registrar_pago(
                    datos={
                        "id_presupuesto": presupuesto,
                        "id_medio_pago": form.cleaned_data["id_medio_pago"],
                        "monto": form.cleaned_data["monto"],
                        "numero_comprobante": form.cleaned_data.get("numero_comprobante", ""),
                        "observacion": form.cleaned_data.get("observacion", ""),
                        "estado_pago": "vigente",
                    },
                    usuario=request.user,
                    request=request,
                )
                messages.success(request, f"Pago de ${pago.monto:,.0f} CLP registrado correctamente.")
                return redirect("presupuestos:detalle", pk=presupuesto_id)
            except Exception as e:
                messages.error(request, str(e))
        return render(request, self.template_name, {"form": form, "presupuesto": presupuesto, "caja_abierta": caja_abierta})


class PagoAnularView(RolRequeridoMixin, View):
    roles_permitidos = ["cajero", "administrativo", "recepcionista", "administrador"]
    template_name = "pagos/pago_anular.html"

    def get(self, request, pk):
        pago = get_object_or_404(Pago.objects.select_related(
            "id_presupuesto", "id_medio_pago", "id_usuario_registra__id_persona"
        ), pk=pk)
        if pago.estado_pago == "anulado":
            messages.warning(request, "Este pago ya está anulado.")
            return redirect("presupuestos:detalle", pk=pago.id_presupuesto_id)
        return render(request, self.template_name, {"pago": pago})

    def post(self, request, pk):
        pago = get_object_or_404(Pago, pk=pk)
        presupuesto_id = pago.id_presupuesto_id
        try:
            PagoService.anular_pago(
                pago=pago,
                usuario=request.user,
                motivo=request.POST.get("motivo", ""),
                request=request,
            )
            messages.success(request, "Pago anulado correctamente.")
        except Exception as e:
            messages.error(request, str(e))
        return redirect("presupuestos:detalle", pk=presupuesto_id)
