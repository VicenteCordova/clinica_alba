"""
apps/caja/services.py

CajaService: lógica de apertura, cierre y movimientos de caja.
"""
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone


class CajaService:

    @staticmethod
    @transaction.atomic
    def abrir_caja(usuario, monto_inicial: Decimal) -> "Caja":
        """
        Abre una caja para el usuario.
        Valida que el usuario no tenga ya una caja abierta (RN-03).
        """
        from apps.caja.models import Caja
        from apps.auditoria.models import Bitacora

        if Caja.objects.filter(
            id_usuario_apertura=usuario,
            estado_caja=Caja.ESTADO_ABIERTA,
        ).exists():
            raise ValidationError(
                "Ya tienes una caja abierta. Debes cerrarla antes de abrir una nueva."
            )

        if monto_inicial < 0:
            raise ValidationError("El monto inicial no puede ser negativo.")

        caja = Caja.objects.create(
            id_usuario_apertura=usuario,
            monto_inicial=monto_inicial,
            estado_caja=Caja.ESTADO_ABIERTA,
            fecha_apertura=timezone.now(),
        )

        Bitacora.registrar(
            usuario=usuario,
            modulo="caja",
            accion="apertura",
            tabla_afectada="cajas",
            id_registro_afectado=caja.id_caja,
            descripcion=f"Caja #{caja.id_caja} abierta con monto inicial ${monto_inicial:,.0f}",
        )

        return caja

    @staticmethod
    @transaction.atomic
    def cerrar_caja(caja, usuario_cierre, monto_final: Decimal) -> "Caja":
        """
        Cierra una caja abierta con el arqueo final.
        Valida coherencia del estado (RN-05).
        """
        from apps.auditoria.models import Bitacora

        if caja.estado_caja != "abierta":
            raise ValidationError("Solo se puede cerrar una caja que esté abierta.")

        if monto_final < 0:
            raise ValidationError("El monto final no puede ser negativo.")

        caja.estado_caja = "cerrada"
        caja.fecha_cierre = timezone.now()
        caja.id_usuario_cierre = usuario_cierre
        caja.monto_final = monto_final
        caja.full_clean()
        caja.save()

        Bitacora.registrar(
            usuario=usuario_cierre,
            modulo="caja",
            accion="cierre",
            tabla_afectada="cajas",
            id_registro_afectado=caja.id_caja,
            descripcion=(
                f"Caja #{caja.id_caja} cerrada. "
                f"Monto final: ${monto_final:,.0f} / "
                f"Calculado: ${caja.saldo_calculado:,.0f}"
            ),
        )

        return caja

    @staticmethod
    @transaction.atomic
    def registrar_movimiento(
        caja,
        tipo_movimiento,
        monto: Decimal,
        usuario,
        descripcion: str = None,
        pago=None,
    ) -> "MovimientoCaja":
        """
        Registra un movimiento en la caja activa.
        Valida reglas de negocio para movimientos ligados a pagos (RN-04).
        """
        from apps.caja.models import MovimientoCaja
        from apps.auditoria.models import Bitacora

        if caja.estado_caja != "abierta":
            raise ValidationError(
                "No se pueden registrar movimientos en una caja cerrada."
            )

        if monto <= 0:
            raise ValidationError("El monto del movimiento debe ser mayor que 0.")

        if pago:
            if tipo_movimiento.nombre != "ingreso":
                raise ValidationError(
                    "Un movimiento asociado a un pago debe ser de tipo ingreso."
                )
            if monto != pago.monto:
                raise ValidationError(
                    "El monto del movimiento debe coincidir con el monto del pago."
                )

        movimiento = MovimientoCaja(
            id_caja=caja,
            id_tipo_movimiento=tipo_movimiento,
            id_pago=pago,
            descripcion=descripcion,
            monto=monto,
            id_usuario_registra=usuario,
        )
        movimiento.full_clean()
        movimiento.save()

        Bitacora.registrar(
            usuario=usuario,
            modulo="caja",
            accion="movimiento",
            tabla_afectada="movimientos_caja",
            id_registro_afectado=movimiento.id_movimiento_caja,
            descripcion=(
                f"{tipo_movimiento.nombre.capitalize()} ${monto:,.0f} "
                f"en caja #{caja.id_caja}"
            ),
        )

        return movimiento
