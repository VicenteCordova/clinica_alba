"""
apps/core/forms.py

Mixin base para formularios del sistema El Alba.
Aplica automáticamente clases Bootstrap 5.3 a los widgets.
"""
from django import forms


class AlbaFormMixin:
    """Aplica clases CSS de Bootstrap 5.3 automáticamente a todos los campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                current = field.widget.attrs.get('class', '')
                if 'form-select' not in current:
                    field.widget.attrs['class'] = f'{current} form-select'.strip()
            elif isinstance(field.widget, forms.CheckboxInput):
                current = field.widget.attrs.get('class', '')
                if 'form-check-input' not in current:
                    field.widget.attrs['class'] = f'{current} form-check-input'.strip()
            else:
                current = field.widget.attrs.get('class', '')
                if 'form-control' not in current:
                    field.widget.attrs['class'] = f'{current} form-control'.strip()
