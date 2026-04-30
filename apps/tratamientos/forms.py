"""
apps/tratamientos/forms.py
"""
from django import forms
from apps.tratamientos.models import Tratamiento
from apps.core.forms import AlbaFormMixin


class TratamientoForm(AlbaFormMixin, forms.ModelForm):
    class Meta:
        model = Tratamiento
        fields = [
            "codigo", "nombre", "descripcion",
            "valor_referencial", "duracion_estimada_min",
            "estado_tratamiento",
        ]
        widgets = {
            "codigo": forms.TextInput(attrs={"placeholder": "Ej: TRAT-001"}),
            "valor_referencial": forms.NumberInput(attrs={"min": "0", "step": "100"}),
            "duracion_estimada_min": forms.NumberInput(attrs={"min": "5", "placeholder": "30"}),
            "descripcion": forms.TextInput(attrs={"placeholder": "Descripción breve del tratamiento"}),
        }
