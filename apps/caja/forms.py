"""
apps/caja/forms.py
"""
from django import forms
from apps.caja.models import TipoMovimientoCaja
from apps.core.forms import AlbaFormMixin



class AbrirCajaForm(AlbaFormMixin, forms.Form):
    monto_inicial = forms.DecimalField(
        min_value=0,
        max_digits=14,
        decimal_places=2,
        label="Monto inicial ($)",
        initial=0,
        widget=forms.NumberInput(attrs={"placeholder": "0", "min": "0", "class": "form-control"}),
    )


class CerrarCajaForm(AlbaFormMixin, forms.Form):
    monto_final = forms.DecimalField(
        min_value=0,
        max_digits=14,
        decimal_places=2,
        label="Monto arqueo ($)",
        widget=forms.NumberInput(attrs={"placeholder": "0", "min": "0", "class": "form-control"}),
    )


class MovimientoCajaForm(AlbaFormMixin, forms.Form):
    id_tipo_movimiento = forms.ModelChoiceField(
        queryset=TipoMovimientoCaja.objects.all(),
        label="Tipo",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    monto = forms.DecimalField(
        min_value=1, max_digits=14, decimal_places=2, label="Monto ($)",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "0"}),
    )
    descripcion = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Descripción",
    )
