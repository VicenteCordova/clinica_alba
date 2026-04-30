"""
apps/imagenologia/forms.py
"""
import os
from django import forms
from django.core.exceptions import ValidationError
from .models import ExamenImagenologico, ArchivoExamenImagenologico, TipoExamenImagenologico
from apps.core.forms import AlbaFormMixin


# Extensiones permitidas en Fase 1
EXTENSIONES_PERMITIDAS = ['.pdf', '.jpg', '.jpeg', '.png', '.zip', '.dcm', '.dicom']
MAX_UPLOAD_SIZE = 50 * 1024 * 1024 # 50 MB por archivo por defecto

def validar_archivo_clinico(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in EXTENSIONES_PERMITIDAS:
        raise ValidationError(f"Extensión '{ext}' no permitida. Use: {', '.join(EXTENSIONES_PERMITIDAS)}")
    
    if value.size > MAX_UPLOAD_SIZE:
        max_mb = MAX_UPLOAD_SIZE / (1024 * 1024)
        raise ValidationError(f"El archivo excede el tamaño máximo permitido de {max_mb} MB.")


class ExamenForm(AlbaFormMixin, forms.ModelForm):
    class Meta:
        model = ExamenImagenologico
        fields = [
            "tipo_examen", "fecha_examen", "centro_radiologico",
            "titulo", "descripcion", "observacion_clinica"
        ]
        widgets = {
            "fecha_examen": forms.DateInput(attrs={"type": "date"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "observacion_clinica": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo_examen"].queryset = TipoExamenImagenologico.objects.filter(estado="activo")
        self.fields["tipo_examen"].required = True
        self.fields["fecha_examen"].required = True


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleArchivoForm(AlbaFormMixin, forms.Form):
    archivos = forms.FileField(
        widget=MultipleFileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png,.zip,.dcm,.dicom'}),
        required=False,
        help_text="Archivos permitidos: PDF, JPG, PNG, ZIP, DICOM. Tamaño máximo: 50MB."
    )

    def clean_archivos(self):
        archivos = self.files.getlist('archivos')
        for archivo in archivos:
            validar_archivo_clinico(archivo)
        return archivos
