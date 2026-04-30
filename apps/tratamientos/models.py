"""
apps/tratamientos/models.py

Tablas: tratamientos, planes_tratamiento, plan_tratamiento_detalle
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Tratamiento(models.Model):
    """Tabla: tratamientos"""

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_CHOICES = [(ESTADO_ACTIVO, "Activo"), (ESTADO_INACTIVO, "Inactivo")]

    id_tratamiento = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=200, null=True, blank=True)
    valor_referencial = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_estimada_min = models.PositiveSmallIntegerField(null=True, blank=True)
    estado_tratamiento = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )

    class Meta:
        db_table = "tratamientos"
        verbose_name = "Tratamiento"
        verbose_name_plural = "Tratamientos"
        ordering = ["nombre"]

    def __str__(self):
        return f"[{self.codigo}] {self.nombre}"

    def clean(self):
        if self.valor_referencial is not None and self.valor_referencial < 0:
            raise ValidationError(
                {"valor_referencial": "El valor no puede ser negativo."}
            )
        if self.duracion_estimada_min is not None and self.duracion_estimada_min <= 0:
            raise ValidationError(
                {"duracion_estimada_min": "La duración debe ser mayor que 0."}
            )


class PlanTratamiento(models.Model):
    """Tabla: planes_tratamiento"""

    ESTADO_ACTIVO = "activo"
    ESTADO_CERRADO = "cerrado"
    ESTADO_ANULADO = "anulado"
    ESTADO_BORRADOR = "borrador"
    ESTADO_PROPUESTO = "propuesto"
    ESTADO_ACEPTADO_PARCIAL = "aceptado_parcial"
    ESTADO_ACEPTADO = "aceptado"
    ESTADO_RECHAZADO = "rechazado"
    ESTADO_EN_CURSO = "en_curso"
    ESTADO_SUSPENDIDO = "suspendido"
    ESTADO_FINALIZADO = "finalizado"
    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_CERRADO, "Cerrado"),
        (ESTADO_ANULADO, "Anulado"),
        (ESTADO_BORRADOR, "Borrador"),
        (ESTADO_PROPUESTO, "Propuesto"),
        (ESTADO_ACEPTADO_PARCIAL, "Aceptado parcialmente"),
        (ESTADO_ACEPTADO, "Aceptado"),
        (ESTADO_RECHAZADO, "Rechazado"),
        (ESTADO_EN_CURSO, "En curso"),
        (ESTADO_SUSPENDIDO, "Suspendido"),
        (ESTADO_FINALIZADO, "Finalizado"),
    ]

    id_plan_tratamiento = models.AutoField(primary_key=True)
    id_ficha_clinica = models.ForeignKey(
        "fichas.FichaClinica",
        db_column="id_ficha_clinica",
        on_delete=models.RESTRICT,
        related_name="planes_tratamiento",
    )
    id_odontologo = models.ForeignKey(
        "odontologos.Odontologo",
        db_column="id_odontologo",
        on_delete=models.RESTRICT,
        related_name="planes_tratamiento",
    )
    id_cita = models.ForeignKey(
        "agenda.Cita",
        db_column="id_cita",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planes_tratamiento",
    )
    id_evolucion = models.ForeignKey(
        "fichas.EvolucionClinica",
        db_column="id_evolucion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planes_tratamiento",
    )
    id_odontograma = models.ForeignKey(
        "odontograma.Odontograma",
        db_column="id_odontograma",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planes_tratamiento",
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)
    estado_plan = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )
    observaciones = models.TextField(null=True, blank=True)
    fecha_anulacion = models.DateTimeField(null=True, blank=True)
    id_usuario_anula = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_anula",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="planes_anulados",
    )
    motivo_anulacion = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = "planes_tratamiento"
        verbose_name = "Plan de Tratamiento"
        verbose_name_plural = "Planes de Tratamiento"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["id_ficha_clinica"], name="idx_planes_ficha"),
            models.Index(fields=["id_odontologo"], name="idx_planes_odontologo"),
        ]

    def __str__(self):
        return (
            f"Plan #{self.id_plan_tratamiento} — "
            f"{self.id_ficha_clinica.id_paciente.nombre_completo}"
        )

    @property
    def total_estimado(self):
        """Suma de subtotales de todos los ítems del plan."""
        return sum(d.subtotal for d in self.detalles.all())



class PlanTratamientoDetalle(models.Model):
    """Tabla: plan_tratamiento_detalle"""

    ESTADO_PENDIENTE = "pendiente"
    ESTADO_APROBADO = "aprobado"
    ESTADO_EN_CURSO = "en_curso"
    ESTADO_REALIZADO = "realizado"
    ESTADO_SUSPENDIDO = "suspendido"
    ESTADO_RECHAZADO = "rechazado"
    ESTADO_ANULADO = "anulado"
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_APROBADO, "Aprobado"),
        (ESTADO_EN_CURSO, "En curso"),
        (ESTADO_REALIZADO, "Realizado"),
        (ESTADO_SUSPENDIDO, "Suspendido"),
        (ESTADO_RECHAZADO, "Rechazado"),
        (ESTADO_ANULADO, "Anulado"),
    ]

    id_plan_detalle = models.AutoField(primary_key=True)
    id_plan_tratamiento = models.ForeignKey(
        PlanTratamiento,
        db_column="id_plan_tratamiento",
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    id_tratamiento = models.ForeignKey(
        Tratamiento,
        db_column="id_tratamiento",
        on_delete=models.RESTRICT,
        related_name="plan_detalles",
    )
    codigo_pieza_dental = models.ForeignKey(
        "odontograma.PiezaDental",
        db_column="codigo_pieza_dental",
        to_field="codigo_pieza_dental",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="plan_detalles",
    )
    cantidad = models.PositiveIntegerField(default=1)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    estado_detalle = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE
    )
    nivel_prioridad = models.PositiveSmallIntegerField(null=True, blank=True)
    observaciones = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = "plan_tratamiento_detalle"
        verbose_name = "Detalle de Plan de Tratamiento"
        verbose_name_plural = "Detalles de Plan de Tratamiento"
        indexes = [
            models.Index(fields=["id_plan_tratamiento"], name="idx_plan_detalle_plan"),
        ]

    def __str__(self):
        return f"{self.id_tratamiento.nombre} × {self.cantidad}"

    @property
    def subtotal(self):
        return self.cantidad * self.valor_unitario

    def clean(self):
        if self.cantidad is not None and self.cantidad <= 0:
            raise ValidationError({"cantidad": "La cantidad debe ser mayor que 0."})
        if self.valor_unitario is not None and self.valor_unitario < 0:
            raise ValidationError(
                {"valor_unitario": "El valor unitario no puede ser negativo."}
            )
        if self.nivel_prioridad is not None and not (1 <= self.nivel_prioridad <= 5):
            raise ValidationError(
                {"nivel_prioridad": "La prioridad debe estar entre 1 y 5."}
            )
