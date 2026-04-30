"""
apps/presupuestos/models.py

Tablas: presupuestos, presupuesto_detalle
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Presupuesto(models.Model):
    """
    Tabla: presupuestos

    Restricción crítica: monto_final = monto_bruto - descuento_total
    Se calcula y valida en PresupuestoService y en el formulario.
    """

    ESTADO_VIGENTE = "vigente"
    ESTADO_VENCIDO = "vencido"
    ESTADO_ACEPTADO = "aceptado"
    ESTADO_RECHAZADO = "rechazado"
    ESTADO_ANULADO = "anulado"
    ESTADO_PAGADO_PARCIAL = "pagado_parcial"
    ESTADO_PAGADO_TOTAL = "pagado_total"
    ESTADO_CHOICES = [
        (ESTADO_VIGENTE, "Vigente"),
        (ESTADO_VENCIDO, "Vencido"),
        (ESTADO_ACEPTADO, "Aceptado"),
        (ESTADO_RECHAZADO, "Rechazado"),
        (ESTADO_ANULADO, "Anulado"),
        (ESTADO_PAGADO_PARCIAL, "Pagado parcial"),
        (ESTADO_PAGADO_TOTAL, "Pagado total"),
    ]

    id_presupuesto = models.AutoField(primary_key=True)
    id_plan_tratamiento = models.ForeignKey(
        "tratamientos.PlanTratamiento",
        db_column="id_plan_tratamiento",
        on_delete=models.RESTRICT,
        related_name="presupuestos",
    )
    numero_presupuesto = models.CharField(max_length=30, unique=True)
    fecha_emision = models.DateTimeField(default=timezone.now)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    monto_bruto = models.DecimalField(max_digits=10, decimal_places=2)
    descuento_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_final = models.DecimalField(max_digits=10, decimal_places=2)
    estado_presupuesto = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_VIGENTE
    )
    id_usuario_emite = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_emite",
        on_delete=models.RESTRICT,
        related_name="presupuestos_emitidos",
    )
    fecha_anulacion = models.DateTimeField(null=True, blank=True)
    id_usuario_anula = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_anula",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="presupuestos_anulados",
    )
    motivo_anulacion = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = "presupuestos"
        verbose_name = "Presupuesto"
        verbose_name_plural = "Presupuestos"
        ordering = ["-fecha_emision"]
        indexes = [
            models.Index(fields=["id_plan_tratamiento"], name="idx_presupuestos_plan"),
        ]

    def __str__(self):
        return f"Presupuesto {self.numero_presupuesto}"

    def clean(self):
        if self.monto_bruto is not None and self.monto_bruto < 0:
            raise ValidationError({"monto_bruto": "El monto bruto no puede ser negativo."})
        if self.descuento_total is not None and self.descuento_total < 0:
            raise ValidationError(
                {"descuento_total": "El descuento no puede ser negativo."}
            )
        if (
            self.monto_bruto is not None
            and self.descuento_total is not None
            and self.monto_final is not None
        ):
            esperado = self.monto_bruto - self.descuento_total
            if abs(self.monto_final - esperado) > 0.01:
                raise ValidationError(
                    "El monto final debe ser igual a monto bruto − descuento total."
                )

    @property
    def total_pagado(self):
        return self.pagos.filter(estado_pago="vigente").aggregate(
            total=models.Sum("monto")
        )["total"] or 0

    @property
    def saldo_pendiente(self):
        return self.monto_final - self.total_pagado


class PresupuestoDetalle(models.Model):
    """
    Tabla: presupuesto_detalle

    Restricción: subtotal = cantidad × precio_unitario
    Se valida en el formulario y en el servicio.
    """

    id_presupuesto_detalle = models.AutoField(primary_key=True)
    id_presupuesto = models.ForeignKey(
        Presupuesto,
        db_column="id_presupuesto",
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    id_plan_detalle = models.ForeignKey(
        "tratamientos.PlanTratamientoDetalle",
        db_column="id_plan_detalle",
        on_delete=models.RESTRICT,
        related_name="presupuesto_detalles",
    )
    descripcion_item = models.CharField(max_length=200)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "presupuesto_detalle"
        unique_together = [("id_presupuesto", "id_plan_detalle")]
        verbose_name = "Detalle de Presupuesto"
        verbose_name_plural = "Detalles de Presupuesto"

    def __str__(self):
        return f"{self.descripcion_item} × {self.cantidad}"

    def clean(self):
        if self.cantidad is not None and self.cantidad <= 0:
            raise ValidationError({"cantidad": "La cantidad debe ser mayor que 0."})
        if self.precio_unitario is not None and self.precio_unitario < 0:
            raise ValidationError({"precio_unitario": "El precio no puede ser negativo."})
        if (
            self.cantidad is not None
            and self.precio_unitario is not None
            and self.subtotal is not None
        ):
            esperado = self.cantidad * self.precio_unitario
            if abs(self.subtotal - esperado) > 0.01:
                raise ValidationError(
                    "El subtotal debe ser igual a cantidad × precio unitario."
                )
