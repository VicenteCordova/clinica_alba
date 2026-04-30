"""
apps/agenda/models.py

Tablas: box, tipos_atencion, estados_cita, citas, historial_citas
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Box(models.Model):
    """Tabla: box"""

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_CHOICES = [(ESTADO_ACTIVO, "Activo"), (ESTADO_INACTIVO, "Inactivo")]

    id_box = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    ubicacion = models.CharField(max_length=100, null=True, blank=True)
    descripcion = models.CharField(max_length=150, null=True, blank=True)
    estado_box = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )

    class Meta:
        db_table = "box"
        verbose_name = "Box"
        verbose_name_plural = "Boxes"

    def __str__(self):
        return self.nombre


class TipoAtencion(models.Model):
    """Tabla: tipos_atencion"""

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_CHOICES = [(ESTADO_ACTIVO, "Activo"), (ESTADO_INACTIVO, "Inactivo")]

    id_tipo_atencion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.CharField(max_length=150, null=True, blank=True)
    duracion_estimada_min = models.PositiveSmallIntegerField()
    estado_tipo_atencion = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )

    class Meta:
        db_table = "tipos_atencion"
        verbose_name = "Tipo de Atención"
        verbose_name_plural = "Tipos de Atención"

    def __str__(self):
        return self.nombre

    def clean(self):
        if self.duracion_estimada_min is not None and self.duracion_estimada_min <= 0:
            raise ValidationError(
                {"duracion_estimada_min": "La duración debe ser mayor que 0."}
            )


class EstadoCita(models.Model):
    """Tabla: estados_cita"""

    id_estado_cita = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)
    descripcion = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "estados_cita"
        verbose_name = "Estado de Cita"
        verbose_name_plural = "Estados de Cita"

    def __str__(self):
        return self.nombre


class Cita(models.Model):
    """
    Tabla: citas

    Regla de solapamiento (RN-01 actualizada):
    Los estados 'cancelada' y 'reprogramada' LIBERAN el slot.
    Solo bloquean: pendiente, confirmada, atendida.
    La validación se hace en CitaService antes del save().
    El trigger SQL en BD actúa como fallback.
    """

    id_cita = models.AutoField(primary_key=True)
    id_paciente = models.ForeignKey(
        "pacientes.Paciente",
        db_column="id_paciente",
        on_delete=models.RESTRICT,
        related_name="citas",
    )
    id_odontologo = models.ForeignKey(
        "odontologos.Odontologo",
        db_column="id_odontologo",
        on_delete=models.RESTRICT,
        related_name="citas",
    )
    id_box = models.ForeignKey(
        Box,
        db_column="id_box",
        on_delete=models.RESTRICT,
        related_name="citas",
    )
    id_tipo_atencion = models.ForeignKey(
        TipoAtencion,
        db_column="id_tipo_atencion",
        on_delete=models.RESTRICT,
        related_name="citas",
    )
    id_estado_cita = models.ForeignKey(
        EstadoCita,
        db_column="id_estado_cita",
        on_delete=models.RESTRICT,
        related_name="citas",
    )
    fecha_hora_inicio = models.DateTimeField()
    fecha_hora_fin = models.DateTimeField()
    motivo_consulta = models.CharField(max_length=200, null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    id_usuario_registra = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_registra",
        on_delete=models.RESTRICT,
        related_name="citas_registradas",
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "citas"
        verbose_name = "Cita"
        verbose_name_plural = "Citas"
        indexes = [
            models.Index(fields=["id_paciente"], name="idx_citas_paciente"),
            models.Index(fields=["id_odontologo"], name="idx_citas_odontologo"),
            models.Index(fields=["id_box"], name="idx_citas_box"),
            models.Index(fields=["id_estado_cita"], name="idx_citas_estado"),
            models.Index(fields=["fecha_hora_inicio"], name="idx_citas_fecha"),
            models.Index(
                fields=["fecha_hora_inicio", "fecha_hora_fin"],
                name="idx_citas_inicio_fin",
            ),
        ]

    def __str__(self):
        return (
            f"Cita #{self.id_cita} — "
            f"{self.id_paciente} con {self.id_odontologo} "
            f"el {self.fecha_hora_inicio:%d/%m/%Y %H:%M}"
        )

    def clean(self):
        if self.fecha_hora_fin and self.fecha_hora_inicio:
            if self.fecha_hora_fin <= self.fecha_hora_inicio:
                raise ValidationError(
                    "La hora de fin debe ser posterior a la hora de inicio."
                )


class HistorialCita(models.Model):
    """Tabla: historial_citas"""

    id_historial_cita = models.AutoField(primary_key=True)
    id_cita = models.ForeignKey(
        Cita,
        db_column="id_cita",
        on_delete=models.CASCADE,
        related_name="historial",
    )
    id_estado_anterior = models.ForeignKey(
        EstadoCita,
        db_column="id_estado_anterior",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="historial_anteriores",
    )
    id_estado_nuevo = models.ForeignKey(
        EstadoCita,
        db_column="id_estado_nuevo",
        on_delete=models.RESTRICT,
        related_name="historial_nuevos",
    )
    motivo_cambio = models.CharField(max_length=200, null=True, blank=True)
    fecha_cambio = models.DateTimeField(default=timezone.now)
    id_usuario_responsable = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_responsable",
        on_delete=models.RESTRICT,
        related_name="historial_citas_responsable",
    )

    class Meta:
        db_table = "historial_citas"
        verbose_name = "Historial de Cita"
        verbose_name_plural = "Historial de Citas"
        ordering = ["-fecha_cambio"]

    def __str__(self):
        ant = self.id_estado_anterior.nombre if self.id_estado_anterior else "—"
        return f"Cita #{self.id_cita_id}: {ant} → {self.id_estado_nuevo.nombre}"

    def clean(self):
        if (
            self.id_estado_anterior
            and self.id_estado_nuevo
            and self.id_estado_anterior == self.id_estado_nuevo
        ):
            raise ValidationError(
                "El estado anterior y el nuevo no pueden ser el mismo."
            )
