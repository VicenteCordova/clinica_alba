"""
apps/odontologos/models.py

Tablas: especialidades, odontologos, odontologo_especialidad, horarios_odontologo
"""
from django.db import models


class Especialidad(models.Model):
    """Tabla: especialidades"""

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_CHOICES = [(ESTADO_ACTIVO, "Activo"), (ESTADO_INACTIVO, "Inactivo")]

    id_especialidad = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.CharField(max_length=150, null=True, blank=True)
    estado_especialidad = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )

    class Meta:
        db_table = "especialidades"
        verbose_name = "Especialidad"
        verbose_name_plural = "Especialidades"

    def __str__(self):
        return self.nombre


class Odontologo(models.Model):
    """Tabla: odontologos"""

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_SUSPENDIDO = "suspendido"
    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_INACTIVO, "Inactivo"),
        (ESTADO_SUSPENDIDO, "Suspendido"),
    ]

    id_odontologo = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField(
        "accounts.Usuario",
        db_column="id_usuario",
        on_delete=models.RESTRICT,
        related_name="odontologo",
    )
    numero_registro = models.CharField(max_length=30, unique=True)
    duracion_cita_base_min = models.PositiveSmallIntegerField()
    estado_profesional = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )
    especialidades = models.ManyToManyField(
        Especialidad,
        through="OdontologoEspecialidad",
        related_name="odontologos",
    )

    class Meta:
        db_table = "odontologos"
        verbose_name = "Odontólogo"
        verbose_name_plural = "Odontólogos"

    def __str__(self):
        return f"Dr(a). {self.id_usuario.nombre_completo}"

    @property
    def nombre_completo(self):
        return self.id_usuario.nombre_completo

    @property
    def especialidad_principal(self):
        rel = self.odontologo_especialidades.filter(es_principal=True).first()
        return rel.especialidad if rel else None


class OdontologoEspecialidad(models.Model):
    """Tabla: odontologo_especialidad (M2M con campo extra es_principal)"""

    id_odontologo = models.ForeignKey(
        Odontologo,
        db_column="id_odontologo",
        on_delete=models.CASCADE,
        related_name="odontologo_especialidades",
    )
    especialidad = models.ForeignKey(
        Especialidad,
        db_column="id_especialidad",
        on_delete=models.RESTRICT,
        related_name="odontologo_especialidades",
    )
    es_principal = models.BooleanField(default=False)

    class Meta:
        db_table = "odontologo_especialidad"
        unique_together = [("id_odontologo", "especialidad")]
        verbose_name = "Especialidad de Odontólogo"
        verbose_name_plural = "Especialidades de Odontólogos"

    def __str__(self):
        principal = " (principal)" if self.es_principal else ""
        return f"{self.id_odontologo} → {self.especialidad}{principal}"


class HorarioOdontologo(models.Model):
    """Tabla: horarios_odontologo"""

    DIA_LUNES = 1
    DIA_MARTES = 2
    DIA_MIERCOLES = 3
    DIA_JUEVES = 4
    DIA_VIERNES = 5
    DIA_SABADO = 6
    DIA_DOMINGO = 7
    DIA_CHOICES = [
        (DIA_LUNES, "Lunes"),
        (DIA_MARTES, "Martes"),
        (DIA_MIERCOLES, "Miércoles"),
        (DIA_JUEVES, "Jueves"),
        (DIA_VIERNES, "Viernes"),
        (DIA_SABADO, "Sábado"),
        (DIA_DOMINGO, "Domingo"),
    ]

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_CHOICES = [(ESTADO_ACTIVO, "Activo"), (ESTADO_INACTIVO, "Inactivo")]

    id_horario = models.AutoField(primary_key=True)
    id_odontologo = models.ForeignKey(
        Odontologo,
        db_column="id_odontologo",
        on_delete=models.CASCADE,
        related_name="horarios",
    )
    dia_semana = models.PositiveSmallIntegerField(choices=DIA_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado_horario = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )

    class Meta:
        db_table = "horarios_odontologo"
        unique_together = [("id_odontologo", "dia_semana", "hora_inicio", "hora_fin")]
        verbose_name = "Horario de Odontólogo"
        verbose_name_plural = "Horarios de Odontólogos"

    def __str__(self):
        return (
            f"{self.id_odontologo} — "
            f"{self.get_dia_semana_display()} "
            f"{self.hora_inicio:%H:%M}-{self.hora_fin:%H:%M}"
        )

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.hora_fin and self.hora_inicio and self.hora_fin <= self.hora_inicio:
            raise ValidationError("La hora de fin debe ser posterior a la hora de inicio.")
