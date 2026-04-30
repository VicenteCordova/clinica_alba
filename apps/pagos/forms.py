"""
apps/pagos/forms.py
"""
from django import forms
from apps.pagos.models import MedioPago
from apps.core.forms import AlbaFormMixin


class PagoForm(AlbaFormMixin, forms.Form):
    id_medio_pago = forms.ModelChoiceField(
        queryset=MedioPago.objects.filter(estado_medio_pago="activo"),
        label="Medio de pago",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    monto = forms.DecimalField(
        min_value=1,
        max_digits=14,
        decimal_places=2,
        label="Monto ($)",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "0"}),
    )
    numero_comprobante = forms.CharField(
        required=False,
        max_length=100,
        label="Numero de comprobante",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    observacion = forms.CharField(
        required=False,
        max_length=200,
        label="Observacion",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )
