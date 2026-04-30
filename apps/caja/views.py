"""
apps/caja/views.py
"""
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib import messages

from apps.core.mixins import LoginRequeridoMixin, RolRequeridoMixin
from apps.caja.models import Caja, MovimientoCaja
from apps.caja.services import CajaService
from apps.caja.forms import AbrirCajaForm, CerrarCajaForm, MovimientoCajaForm


class CajaListView(RolRequeridoMixin, ListView):
    roles_permitidos = ["cajero", "administrativo", "recepcionista", "administrador"]
    template_name = "caja/lista.html"
    context_object_name = "cajas"
    paginate_by = 20
    queryset = Caja.objects.select_related(
        "id_usuario_apertura__id_persona"
    ).order_by("-fecha_apertura")


class AbrirCajaView(RolRequeridoMixin, View):
    roles_permitidos = ["cajero", "administrativo", "recepcionista", "administrador"]
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


class CajaDetalleView(RolRequeridoMixin, View):
    roles_permitidos = ["cajero", "administrativo", "recepcionista", "administrador"]
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


class CerrarCajaView(RolRequeridoMixin, View):
    roles_permitidos = ["cajero", "administrativo", "recepcionista", "administrador"]
    def post(self, request, pk):
        caja = get_object_or_404(Caja, pk=pk)
        form = CerrarCajaForm(data=request.POST)
        if form.is_valid():
            try:
                CajaService.cerrar_caja(
                    caja=caja,
                    usuario_cierre=request.user,
                    monto_final=form.cleaned_data["monto_final"],
                )
                messages.success(request, f"Caja #{caja.id_caja} cerrada correctamente.")
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Error en los datos del formulario de cierre.")
        return redirect("caja:detalle", pk=pk)


class MovimientoCajaView(RolRequeridoMixin, View):
    roles_permitidos = ["cajero", "administrativo", "recepcionista", "administrador"]
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
