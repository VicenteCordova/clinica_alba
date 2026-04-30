"""
apps/personas/models.py

Tablas: sexos, personas
"""
from django.db import models
from django.utils import timezone


class Sexo(models.Model):
    """Tabla: sexos"""

    id_sexo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=20, unique=True)

    class Meta:
        db_table = "sexos"
        verbose_name = "Sexo"
        verbose_name_plural = "Sexos"

    def __str__(self):
        return self.nombre


class Persona(models.Model):
    """Tabla: personas"""

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_INACTIVO, "Inactivo"),
    ]

    id_persona = models.AutoField(primary_key=True)
    rut = models.CharField(max_length=12, unique=True)
    nombres = models.CharField(max_length=80)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    id_sexo = models.ForeignKey(
        Sexo,
        db_column="id_sexo",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="personas",
    )
    correo = models.CharField(max_length=120, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    direccion = models.CharField(max_length=150, null=True, blank=True)
    comuna = models.CharField(max_length=80, null=True, blank=True)
    ciudad = models.CharField(max_length=80, null=True, blank=True)
    estado_persona = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "personas"
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        indexes = [
            models.Index(fields=["rut"], name="idx_personas_rut"),
            models.Index(fields=["id_sexo"], name="idx_personas_id_sexo"),
        ]

    def __str__(self):
        return self.nombre_completo

    @property
    def nombre_completo(self) -> str:
        partes = [self.nombres, self.apellido_paterno]
        if self.apellido_materno:
            partes.append(self.apellido_materno)
        return " ".join(partes)

    @property
    def edad(self):
        from apps.core.utils import calcular_edad
        return calcular_edad(self.fecha_nacimiento)
