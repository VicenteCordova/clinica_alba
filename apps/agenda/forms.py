"""
apps/agenda/forms.py
"""
from django import forms
from django.core.exceptions import ValidationError
from apps.agenda.models import Cita, Box, EstadoCita, TipoAtencion
from apps.pacientes.models import Paciente
from apps.odontologos.models import Odontologo
from apps.core.forms import AlbaFormMixin



class CitaForm(AlbaFormMixin, forms.ModelForm):
    class Meta:
        model = Cita
        fields = [
            "id_paciente", "id_odontologo", "id_box",
            "id_tipo_atencion", "id_estado_cita",
            "fecha_hora_inicio", "fecha_hora_fin",
            "motivo_consulta", "observaciones",
        ]
        widgets = {
            "fecha_hora_inicio": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "fecha_hora_fin": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "motivo_consulta": forms.TextInput(attrs={"placeholder": "Ej: Dolor molar, control..."}),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_paciente"].queryset = (
            Paciente.objects.select_related("id_persona")
            .filter(id_persona__estado_persona="activo")
            .order_by("id_persona__apellido_paterno")
        )
        self.fields["id_odontologo"].queryset = (
            Odontologo.objects.filter(estado_profesional="activo")
            .select_related("id_usuario__id_persona")
        )
        self.fields["id_box"].queryset = Box.objects.filter(estado_box="activo")
        self.fields["id_estado_cita"].queryset = EstadoCita.objects.all()
        self.fields["id_tipo_atencion"].queryset = TipoAtencion.objects.filter(estado_tipo_atencion="activo")
        self.fields["fecha_hora_inicio"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["fecha_hora_fin"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get("fecha_hora_inicio")
        fin = cleaned.get("fecha_hora_fin")
        if inicio and fin:
            if fin <= inicio:
                raise ValidationError("La hora de fin debe ser posterior al inicio.")
            duracion_min = (fin - inicio).total_seconds() / 60
            if duracion_min < 15:
                raise ValidationError("La duración mínima es 15 minutos.")
        return cleaned


class CambiarEstadoCitaForm(AlbaFormMixin, forms.Form):
    nuevo_estado = forms.ModelChoiceField(queryset=EstadoCita.objects.all(), label="Nuevo estado")
    motivo_cambio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Motivo",
    )
