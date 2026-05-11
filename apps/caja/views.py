"""
apps/caja/views.py
"""
from decimal import Decimal
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from django.utils import timezone

from apps.core.mixins import PermisoRequeridoMixin
from apps.caja.models import Caja, MovimientoCaja, EntradaLibroMayor
from apps.caja.services import CajaService
from apps.caja.forms import AbrirCajaForm, CerrarCajaForm, MovimientoCajaForm


class CajaListView(PermisoRequeridoMixin, ListView):
    permission_required = "caja.view_caja"
    template_name = "caja/lista.html"
    context_object_name = "cajas"
    paginate_by = 20
    queryset = Caja.objects.select_related(
        "id_usuario_apertura__id_persona"
    ).order_by("-fecha_apertura")


class AbrirCajaView(PermisoRequeridoMixin, View):
    permission_required = "caja.add_caja"
    template_name = "caja/abrir.html"

    def get(self, request):
        caja_abierta = Caja.objects.filter(
            id_usuario_apertura=request.user,
            estado_caja="abierta",
        ).first()
        return render(request, self.template_name, {
            "form": AbrirCajaForm(),
            "caja_abierta": caja_abierta,
        })

    def post(self, request):
        form = AbrirCajaForm(data=request.POST)
        if form.is_valid():
            try:
                caja = CajaService.abrir_caja(
                    usuario=request.user,
                    monto_inicial=form.cleaned_data["monto_inicial"],
                )
                messages.success(request, f"Caja #{caja.id_caja} abierta correctamente.")
                return redirect("caja:detalle", pk=caja.id_caja)
            except Exception as e:
                messages.error(request, str(e))
        return render(request, self.template_name, {"form": form})


class CajaDetalleView(PermisoRequeridoMixin, View):
    permission_required = "caja.view_caja"
    template_name = "caja/detalle.html"

    def get(self, request, pk):
        caja = get_object_or_404(Caja.objects.select_related("id_usuario_apertura__id_persona"), pk=pk)
        movimientos = MovimientoCaja.objects.filter(id_caja=caja).select_related(
            "id_tipo_movimiento", "id_usuario_registra__id_persona"
        ).order_by("fecha_movimiento")
        return render(request, self.template_name, {
            "caja": caja,
            "movimientos": movimientos,
            "mov_form": MovimientoCajaForm(),
            "cerrar_form": CerrarCajaForm(),
        })


class CerrarCajaView(PermisoRequeridoMixin, View):
    permission_required = "caja.change_caja"
    def post(self, request, pk):
        caja = get_object_or_404(Caja, pk=pk)
        form = CerrarCajaForm(data=request.POST)
        if form.is_valid():
            try:
                CajaService.cerrar_caja(
                    caja=caja,
                    usuario_cierre=request.user,
                    monto_final=form.cleaned_data["monto_final"],
                    observacion_cierre=form.cleaned_data.get("observacion_cierre", ""),
                )
                messages.success(request, f"Caja #{caja.id_caja} cerrada correctamente.")
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Error en los datos del formulario de cierre.")
        return redirect("caja:detalle", pk=pk)


class MovimientoCajaView(PermisoRequeridoMixin, View):
    permission_required = "caja.add_movimientocaja"
    def post(self, request, pk):
        caja = get_object_or_404(Caja, pk=pk)
        form = MovimientoCajaForm(data=request.POST)
        if form.is_valid():
            try:
                CajaService.registrar_movimiento(
                    caja=caja,
                    tipo_movimiento=form.cleaned_data["id_tipo_movimiento"],
                    monto=form.cleaned_data["monto"],
                    descripcion=form.cleaned_data.get("descripcion", ""),
                    usuario=request.user,
                )
                messages.success(request, "Movimiento registrado correctamente.")
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Datos inválidos en el movimiento.")
        return redirect("caja:detalle", pk=pk)


class LibroMayorView(PermisoRequeridoMixin, View):
    """Vista de Libro Mayor filtrable por rango de fechas."""
    permission_required = "caja.view_caja"
    template_name = "caja/libro_mayor.html"

    def get(self, request):
        hoy = timezone.localdate()
        fecha_desde_str = request.GET.get("desde", str(hoy - timedelta(days=30)))
        fecha_hasta_str = request.GET.get("hasta", str(hoy))

        try:
            fecha_desde = date.fromisoformat(fecha_desde_str)
            fecha_hasta = date.fromisoformat(fecha_hasta_str)
        except ValueError:
            fecha_desde = hoy - timedelta(days=30)
            fecha_hasta = hoy

        entradas = (
            EntradaLibroMayor.objects
            .filter(fecha__date__gte=fecha_desde, fecha__date__lte=fecha_hasta)
            .select_related("id_usuario__id_persona", "id_caja", "id_pago")
            .order_by("-fecha")
        )

        total_ingresos = EntradaLibroMayor.objects.ingresos_periodo(fecha_desde, fecha_hasta)
        total_egresos = EntradaLibroMayor.objects.egresos_periodo(fecha_desde, fecha_hasta)
        balance = EntradaLibroMayor.objects.balance_periodo(fecha_desde, fecha_hasta)

        return render(request, self.template_name, {
            "entradas": entradas,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "total_ingresos": total_ingresos,
            "total_egresos": total_egresos,
            "balance": balance,
        })
