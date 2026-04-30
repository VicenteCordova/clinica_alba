"""
apps/pagos/models.py

Tablas: medios_pago, pagos
"""
from django.db import models
from django.utils import timezone


class MedioPago(models.Model):
    """Tabla: medios_pago"""

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_CHOICES = [(ESTADO_ACTIVO, "Activo"), (ESTADO_INACTIVO, "Inactivo")]

    id_medio_pago = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=100, null=True, blank=True)
    estado_medio_pago = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )

    class Meta:
        db_table = "medios_pago"
        verbose_name = "Medio de Pago"
        verbose_name_plural = "Medios de Pago"

    def __str__(self):
        return self.nombre


class Pago(models.Model):
    """
    Tabla: pagos

    Restricción crítica (RN-02):
    suma de pagos vigentes del presupuesto ≤ monto_final.
    Validado en PagoService con select_for_update().
    """

    ESTADO_VIGENTE = "vigente"
    ESTADO_ANULADO = "anulado"
    ESTADO_CHOICES = [
        (ESTADO_VIGENTE, "Vigente"),
        (ESTADO_ANULADO, "Anulado"),
    ]

    id_pago = models.AutoField(primary_key=True)
    id_presupuesto = models.ForeignKey(
        "presupuestos.Presupuesto",
        db_column="id_presupuesto",
        on_delete=models.RESTRICT,
        related_name="pagos",
    )
    id_medio_pago = models.ForeignKey(
        MedioPago,
        db_column="id_medio_pago",
        on_delete=models.RESTRICT,
        related_name="pagos",
    )
    fecha_pago = models.DateTimeField(default=timezone.now)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    numero_comprobante = models.CharField(max_length=50, unique=True, null=True, blank=True)
    observacion = models.CharField(max_length=200, null=True, blank=True)
    estado_pago = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_VIGENTE
    )
    id_usuario_registra = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_registra",
        on_delete=models.RESTRICT,
        related_name="pagos_registrados",
    )
    fecha_anulacion = models.DateTimeField(null=True, blank=True)
    id_usuario_anula = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_anula",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="pagos_anulados",
    )
    motivo_anulacion = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = "pagos"
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-fecha_pago"]
        indexes = [
            models.Index(fields=["id_presupuesto"], name="idx_pagos_presupuesto"),
        ]

    def __str__(self):
        return (
            f"Pago #{self.id_pago} — "
            f"${self.monto:,.0f} ({self.get_estado_pago_display()})"
        )
