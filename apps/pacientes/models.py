"""
apps/pacientes/models.py

Tabla: pacientes
"""
from django.db import models
from django.utils import timezone


class Paciente(models.Model):
    """Tabla: pacientes"""

    id_paciente = models.AutoField(primary_key=True)
    id_persona = models.OneToOneField(
        "personas.Persona",
        db_column="id_persona",
        on_delete=models.RESTRICT,
        related_name="paciente",
    )
    contacto_emergencia_nombre = models.CharField(max_length=120, null=True, blank=True)
    contacto_emergencia_telefono = models.CharField(max_length=20, null=True, blank=True)
    observaciones_administrativas = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "pacientes"
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        indexes = [
            models.Index(fields=["id_persona"], name="idx_pacientes_persona"),
        ]

    def __str__(self):
        return str(self.id_persona)

    @property
    def nombre_completo(self):
        return self.id_persona.nombre_completo

    @property
    def rut(self):
        return self.id_persona.rut

    @property
    def tiene_ficha(self):
        return hasattr(self, "ficha_clinica")
