"""
apps/odontologos/forms.py
"""
from django import forms
from apps.odontologos.models import Odontologo, Especialidad, OdontologoEspecialidad, HorarioOdontologo
from apps.core.forms import AlbaFormMixin


class OdontologoForm(AlbaFormMixin, forms.ModelForm):
    especialidades_sel = forms.ModelMultipleChoiceField(
        queryset=Especialidad.objects.filter(estado_especialidad="activo"),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Especialidades",
    )
    especialidad_principal = forms.ModelChoiceField(
        queryset=Especialidad.objects.filter(estado_especialidad="activo"),
        required=False,
        label="Especialidad principal",
    )

    class Meta:
        model = Odontologo
        fields = ["numero_registro", "duracion_cita_base_min", "estado_profesional"]
        widgets = {
            "duracion_cita_base_min": forms.NumberInput(attrs={"min": "10", "placeholder": "30"}),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)
        if instance:
            self.fields["especialidades_sel"].initial = (
                instance.especialidades.all()
            )
            principal = instance.odontologo_especialidades.filter(es_principal=True).first()
            if principal:
                self.fields["especialidad_principal"].initial = principal.especialidad

    def save_especialidades(self, odontologo):
        """Sincroniza las especialidades seleccionadas."""
        OdontologoEspecialidad.objects.filter(id_odontologo=odontologo).delete()
        especialidades = self.cleaned_data.get("especialidades_sel", [])
        principal = self.cleaned_data.get("especialidad_principal")
        for esp in especialidades:
            OdontologoEspecialidad.objects.create(
                id_odontologo=odontologo,
                especialidad=esp,
                es_principal=(esp == principal),
            )


class HorarioForm(AlbaFormMixin, forms.ModelForm):
    class Meta:
        model = HorarioOdontologo
        fields = ["dia_semana", "hora_inicio", "hora_fin", "estado_horario"]
        widgets = {
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}),
            "hora_fin": forms.TimeInput(attrs={"type": "time"}),
        }
