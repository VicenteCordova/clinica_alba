"""
apps/pacientes/forms.py
"""
from django import forms
from django.core.exceptions import ValidationError

from apps.personas.models import Persona, Sexo
from apps.pacientes.models import Paciente
from apps.core.utils import validar_rut, formatear_rut
from apps.core.forms import AlbaFormMixin



class PersonaBaseForm(AlbaFormMixin, forms.ModelForm):
    class Meta:
        model = Persona
        fields = [
            "rut", "nombres", "apellido_paterno", "apellido_materno",
            "fecha_nacimiento", "id_sexo", "correo", "telefono",
            "direccion", "comuna", "ciudad",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
            "rut": forms.TextInput(attrs={"placeholder": "12.345.678-9"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        campos_obligatorios = [
            "apellido_materno", "fecha_nacimiento", "id_sexo", 
            "telefono", "direccion", "comuna", "ciudad"
        ]
        for campo in campos_obligatorios:
            if campo in self.fields:
                self.fields[campo].required = True

    def clean_rut(self):
        rut = self.cleaned_data.get("rut", "").strip()
        rut_limpio = rut.replace(".", "").replace("-", "").upper()
        if not validar_rut(rut_limpio):
            raise ValidationError("El RUT ingresado no es válido.")
        rut_formateado = formatear_rut(rut_limpio)
        qs = Persona.objects.filter(rut=rut_formateado)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"Ya existe una persona con el RUT {rut_formateado}.")
        return rut_formateado

    def clean_correo(self):
        correo = self.cleaned_data.get("correo")
        if not correo:
            return correo
        qs = Persona.objects.filter(correo=correo)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Este correo ya está registrado.")
        return correo


class PacienteForm(AlbaFormMixin, forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            "contacto_emergencia_nombre",
            "contacto_emergencia_telefono",
            "observaciones_administrativas",
        ]
        widgets = {
            "observaciones_administrativas": forms.Textarea(attrs={"rows": 3}),
        }
