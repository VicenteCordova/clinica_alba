"""
apps/caja/models.py

Tablas: tipos_movimiento_caja, cajas, movimientos_caja
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class TipoMovimientoCaja(models.Model):
    """Tabla: tipos_movimiento_caja"""

    id_tipo_movimiento = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)
    descripcion = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "tipos_movimiento_caja"
        verbose_name = "Tipo de Movimiento de Caja"
        verbose_name_plural = "Tipos de Movimiento de Caja"

    def __str__(self):
        return self.nombre


class Caja(models.Model):
    """
    Tabla: cajas

    Restricciones críticas (RN-03, RN-05):
    - Un usuario no puede tener más de una caja abierta simultánea.
    - Coherencia: si abierta → sin cierre; si cerrada → con cierre y fecha coherente.
    Validado en CajaService.
    """

    ESTADO_ABIERTA = "abierta"
    ESTADO_CERRADA = "cerrada"
    ESTADO_CHOICES = [
        (ESTADO_ABIERTA, "Abierta"),
        (ESTADO_CERRADA, "Cerrada"),
    ]

    id_caja = models.AutoField(primary_key=True)
    fecha_apertura = models.DateTimeField(default=timezone.now)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    monto_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estado_caja = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ABIERTA
    )
    id_usuario_apertura = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_apertura",
        on_delete=models.RESTRICT,
        related_name="cajas_apertura",
    )
    id_usuario_cierre = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_cierre",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="cajas_cierre",
    )

    class Meta:
        db_table = "cajas"
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        ordering = ["-fecha_apertura"]
        indexes = [
            models.Index(
                fields=["id_usuario_apertura"], name="idx_cajas_usuario_apertura"
            ),
        ]

    def __str__(self):
        return (
            f"Caja #{self.id_caja} — "
            f"{self.get_estado_caja_display()} — "
            f"{self.fecha_apertura:%d/%m/%Y %H:%M}"
        )

    def clean(self):
        if self.monto_inicial is not None and self.monto_inicial < 0:
            raise ValidationError(
                {"monto_inicial": "El monto inicial no puede ser negativo."}
            )
        if self.estado_caja == self.ESTADO_ABIERTA:
            if any([self.fecha_cierre, self.id_usuario_cierre_id, self.monto_final]):
                raise ValidationError(
                    "Una caja abierta no puede tener datos de cierre."
                )
        elif self.estado_caja == self.ESTADO_CERRADA:
            if not all([self.fecha_cierre, self.id_usuario_cierre_id, self.monto_final is not None]):
                raise ValidationError(
                    "Una caja cerrada debe tener fecha de cierre, usuario de cierre y monto final."
                )
            if self.fecha_cierre and self.fecha_apertura and self.fecha_cierre < self.fecha_apertura:
                raise ValidationError(
                    "La fecha de cierre no puede ser anterior a la apertura."
                )

    @property
    def total_ingresos(self):
        return (
            self.movimientos.filter(
                id_tipo_movimiento__nombre="ingreso"
            ).aggregate(t=models.Sum("monto"))["t"] or 0
        )

    @property
    def total_egresos(self):
        return (
            self.movimientos.filter(
                id_tipo_movimiento__nombre="egreso"
            ).aggregate(t=models.Sum("monto"))["t"] or 0
        )

    @property
    def saldo_calculado(self):
        return self.monto_inicial + self.total_ingresos - self.total_egresos


class MovimientoCaja(models.Model):
    """
    Tabla: movimientos_caja

    Si id_pago IS NOT NULL:
      - tipo debe ser 'ingreso'
      - monto debe coincidir con el pago
    Validado en CajaService y en clean().
    """

    id_movimiento_caja = models.AutoField(primary_key=True)
    id_caja = models.ForeignKey(
        Caja,
        db_column="id_caja",
        on_delete=models.RESTRICT,
        related_name="movimientos",
    )
    id_tipo_movimiento = models.ForeignKey(
        TipoMovimientoCaja,
        db_column="id_tipo_movimiento",
        on_delete=models.RESTRICT,
        related_name="movimientos",
    )
    id_pago = models.OneToOneField(
        "pagos.Pago",
        db_column="id_pago",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="movimiento_caja",
    )
    descripcion = models.CharField(max_length=150, null=True, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_movimiento = models.DateTimeField(default=timezone.now)
    id_usuario_registra = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_registra",
        on_delete=models.RESTRICT,
        related_name="movimientos_caja_registrados",
    )

    class Meta:
        db_table = "movimientos_caja"
        verbose_name = "Movimiento de Caja"
        verbose_name_plural = "Movimientos de Caja"
        ordering = ["-fecha_movimiento"]
        indexes = [
            models.Index(fields=["id_caja"], name="idx_movimientos_caja"),
        ]

    def __str__(self):
        return (
            f"{self.id_tipo_movimiento.nombre.capitalize()} "
            f"${self.monto:,.0f} — Caja #{self.id_caja_id}"
        )

    def clean(self):
        if self.monto is not None and self.monto <= 0:
            raise ValidationError({"monto": "El monto debe ser mayor que 0."})
        if self.id_pago_id:
            # Verificar tipo 'ingreso'
            if (
                self.id_tipo_movimiento
                and self.id_tipo_movimiento.nombre != "ingreso"
            ):
                raise ValidationError(
                    "Un movimiento asociado a pago debe ser de tipo ingreso."
                )
            # Verificar que el monto coincida
            if self.id_pago and self.monto != self.id_pago.monto:
                raise ValidationError(
                    "El monto del movimiento debe coincidir con el monto del pago."
                )
