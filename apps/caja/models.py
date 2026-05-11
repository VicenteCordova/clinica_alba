"""
apps/caja/models.py

Tablas: tipos_movimiento_caja, cajas, movimientos_caja, libro_mayor
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
    diferencia_arqueo = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="monto_final - saldo_calculado al cierre. Negativo = faltante, positivo = sobrante."
    )
    observacion_cierre = models.CharField(
        max_length=300, null=True, blank=True,
        help_text="Justificación de diferencias en el arqueo."
    )
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

    @property
    def arqueo_con_diferencia(self):
        """True si la diferencia de arqueo es significativa (> 0 en abs)."""
        if self.diferencia_arqueo is None:
            return False
        from decimal import Decimal
        return abs(self.diferencia_arqueo) > Decimal("0")


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


# ─────────────────────────────────────────────
# Libro Mayor
# ─────────────────────────────────────────────

class LibroMayorManager(models.Manager):
    """Manager con helpers para consultas por período."""

    def ingresos_periodo(self, fecha_desde, fecha_hasta):
        from django.db.models import Sum
        return (
            self.filter(
                tipo=EntradaLibroMayor.TIPO_INGRESO,
                fecha__date__gte=fecha_desde,
                fecha__date__lte=fecha_hasta,
            ).aggregate(total=Sum("monto"))["total"] or 0
        )

    def egresos_periodo(self, fecha_desde, fecha_hasta):
        from django.db.models import Sum
        return (
            self.filter(
                tipo=EntradaLibroMayor.TIPO_EGRESO,
                fecha__date__gte=fecha_desde,
                fecha__date__lte=fecha_hasta,
            ).aggregate(total=Sum("monto"))["total"] or 0
        )

    def balance_periodo(self, fecha_desde, fecha_hasta):
        ingresos = self.ingresos_periodo(fecha_desde, fecha_hasta)
        egresos = self.egresos_periodo(fecha_desde, fecha_hasta)
        return ingresos - egresos


class EntradaLibroMayor(models.Model):
    """
    Tabla: libro_mayor

    Registro centralizado de todas las operaciones financieras de la clínica.
    Se crea automáticamente al registrar/anular pagos y al cerrar cajas.
    """

    TIPO_INGRESO = "ingreso"
    TIPO_EGRESO = "egreso"
    TIPO_AJUSTE = "ajuste"
    TIPO_CHOICES = [
        (TIPO_INGRESO, "Ingreso"),
        (TIPO_EGRESO, "Egreso"),
        (TIPO_AJUSTE, "Ajuste"),
    ]

    id_entrada = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.CharField(max_length=300)
    fecha = models.DateTimeField(default=timezone.now)

    # Referencias opcionales para trazabilidad
    id_caja = models.ForeignKey(
        Caja,
        db_column="id_caja",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="entradas_libro_mayor",
    )
    id_pago = models.ForeignKey(
        "pagos.Pago",
        db_column="id_pago",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="entradas_libro_mayor",
    )
    id_usuario = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario",
        on_delete=models.RESTRICT,
        related_name="entradas_libro_mayor",
    )

    objects = LibroMayorManager()

    class Meta:
        db_table = "libro_mayor"
        verbose_name = "Entrada Libro Mayor"
        verbose_name_plural = "Libro Mayor"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["fecha"], name="idx_libro_mayor_fecha"),
            models.Index(fields=["tipo"], name="idx_libro_mayor_tipo"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(monto__gt=0),
                name="chk_libro_mayor_monto_positivo",
            ),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} ${self.monto:,.0f} — {self.fecha:%d/%m/%Y %H:%M}"
