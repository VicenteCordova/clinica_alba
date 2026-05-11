"""
apps/pagos/services.py

PagoService: lógica de validación anti-sobrepago con select_for_update().
Integra Libro Mayor y reversas compensatorias al anular pagos.
"""
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.core.exceptions import ValidationError
from apps.core.enums import EstadoPresupuestoEnum, EstadoPagoEnum


class PagoService:

    @staticmethod
    @transaction.atomic
    def registrar_pago(datos: dict, usuario, request=None) -> "Pago":
        """
        Registra un pago validando que la suma de pagos vigentes
        no supere el monto_final del presupuesto.

        Usa select_for_update() para evitar race conditions concurrentes.
        Registra automáticamente en Libro Mayor si el pago es vigente.

        Args:
            datos: dict con id_presupuesto, id_medio_pago, monto,
                   numero_comprobante (opcional), estado_pago.
            usuario: instancia del Usuario que registra.
        Returns:
            Instancia de Pago creada.
        Raises:
            ValidationError si el pago supera el monto del presupuesto.
        """
        from apps.pagos.models import Pago
        from apps.presupuestos.models import Presupuesto
        from apps.auditoria.models import Bitacora
        from apps.caja.models import Caja, TipoMovimientoCaja, EntradaLibroMayor
        from apps.caja.services import CajaService

        # Bloquear el presupuesto para lectura consistente
        presupuesto = (
            Presupuesto.objects.select_for_update()
            .get(id_presupuesto=datos["id_presupuesto"].id_presupuesto)
        )

        if presupuesto.estado_presupuesto in [EstadoPresupuestoEnum.ANULADO, EstadoPresupuestoEnum.RECHAZADO]:
            raise ValidationError(
                "No se puede registrar un pago en un presupuesto anulado o rechazado."
            )

        # Calcular lo ya pagado (solo pagos vigentes)
        ya_pagado = (
            Pago.objects.filter(
                id_presupuesto=presupuesto,
                estado_pago=EstadoPagoEnum.VIGENTE,
            ).aggregate(total=Sum("monto"))["total"]
            or Decimal("0")
        )

        nuevo_monto = Decimal(str(datos["monto"]))
        estado_nuevo = datos.get("estado_pago", EstadoPagoEnum.VIGENTE)

        if estado_nuevo == EstadoPagoEnum.VIGENTE:
            if (ya_pagado + nuevo_monto) > presupuesto.monto_final:
                saldo = presupuesto.monto_final - ya_pagado
                raise ValidationError(
                    f"El pago de ${nuevo_monto:,.0f} excede el saldo pendiente "
                    f"de ${saldo:,.0f} para el presupuesto "
                    f"{presupuesto.numero_presupuesto}."
                )

        pago = Pago(
            id_presupuesto=presupuesto,
            id_medio_pago=datos["id_medio_pago"],
            monto=nuevo_monto,
            numero_comprobante=datos.get("numero_comprobante"),
            observacion=datos.get("observacion"),
            estado_pago=estado_nuevo,
            id_usuario_registra=usuario,
        )
        pago.full_clean()
        pago.save()

        caja_abierta = None
        if estado_nuevo == EstadoPagoEnum.VIGENTE:
            caja_abierta = Caja.objects.filter(
                id_usuario_apertura=usuario,
                estado_caja=Caja.ESTADO_ABIERTA,
            ).first()
            if caja_abierta:
                tipo_ingreso = TipoMovimientoCaja.objects.filter(nombre="ingreso").first()
                if tipo_ingreso:
                    CajaService.registrar_movimiento(
                        caja=caja_abierta,
                        tipo_movimiento=tipo_ingreso,
                        monto=nuevo_monto,
                        usuario=usuario,
                        descripcion=f"Pago presupuesto {presupuesto.numero_presupuesto}",
                        pago=pago,
                    )

            # Registrar en Libro Mayor
            EntradaLibroMayor.objects.create(
                tipo=EntradaLibroMayor.TIPO_INGRESO,
                monto=nuevo_monto,
                descripcion=f"Pago #{pago.id_pago} — Presupuesto {presupuesto.numero_presupuesto}",
                id_caja=caja_abierta,
                id_pago=pago,
                id_usuario=usuario,
            )

        PagoService.actualizar_estado_presupuesto(presupuesto)

        Bitacora.registrar(
            usuario=usuario,
            modulo="pagos",
            accion="creacion",
            tabla_afectada="pagos",
            id_registro_afectado=pago.id_pago,
            descripcion=(
                f"Pago ${nuevo_monto:,.0f} registrado para "
                f"presupuesto {presupuesto.numero_presupuesto}"
            ),
            request=request,
            paciente=presupuesto.id_plan_tratamiento.id_ficha_clinica.id_paciente,
            cita=presupuesto.id_plan_tratamiento.id_cita,
        )

        return pago

    @staticmethod
    @transaction.atomic
    def anular_pago(pago, usuario, motivo: str = "", request=None) -> "Pago":
        """
        Anula un pago vigente.
        Crea automáticamente una reversa compensatoria (egreso) en la caja activa
        del usuario y registra en el Libro Mayor.
        """
        from apps.auditoria.models import Bitacora
        from apps.caja.models import Caja, TipoMovimientoCaja, EntradaLibroMayor
        from apps.caja.services import CajaService

        if pago.estado_pago == "anulado":
            raise ValidationError("El pago ya está anulado.")

        pago.estado_pago = "anulado"
        from django.utils import timezone
        pago.fecha_anulacion = timezone.now()
        pago.id_usuario_anula = usuario
        pago.motivo_anulacion = motivo
        pago.save(update_fields=["estado_pago", "fecha_anulacion", "id_usuario_anula", "motivo_anulacion"])
        PagoService.actualizar_estado_presupuesto(pago.id_presupuesto)

        # Reversa compensatoria en caja activa del usuario que anula
        caja_abierta = Caja.objects.filter(
            id_usuario_apertura=usuario,
            estado_caja=Caja.ESTADO_ABIERTA,
        ).first()
        if caja_abierta:
            tipo_egreso = TipoMovimientoCaja.objects.filter(nombre="egreso").first()
            if tipo_egreso:
                try:
                    CajaService.registrar_movimiento(
                        caja=caja_abierta,
                        tipo_movimiento=tipo_egreso,
                        monto=pago.monto,
                        usuario=usuario,
                        descripcion=(
                            f"REVERSA — Anulación pago #{pago.id_pago}. "
                            f"Motivo: {motivo or 'Sin motivo'}"
                        ),
                    )
                except ValidationError:
                    pass  # No bloqueamos la anulación si hay problema en caja

        # Registrar reversa en Libro Mayor
        EntradaLibroMayor.objects.create(
            tipo=EntradaLibroMayor.TIPO_EGRESO,
            monto=pago.monto,
            descripcion=f"REVERSA Pago #{pago.id_pago} — Motivo: {motivo or 'Sin motivo'}",
            id_caja=caja_abierta,
            id_pago=pago,
            id_usuario=usuario,
        )

        Bitacora.registrar(
            usuario=usuario,
            modulo="pagos",
            accion="anulacion",
            tabla_afectada="pagos",
            id_registro_afectado=pago.id_pago,
            descripcion=f"Pago #{pago.id_pago} anulado. Motivo: {motivo}",
            request=request,
            paciente=pago.id_presupuesto.id_plan_tratamiento.id_ficha_clinica.id_paciente,
            cita=pago.id_presupuesto.id_plan_tratamiento.id_cita,
        )

        return pago

    @staticmethod
    def actualizar_estado_presupuesto(presupuesto):
        from apps.pagos.models import Pago
        from apps.presupuestos.models import Presupuesto

        total_pagado = presupuesto.total_pagado
        if total_pagado >= presupuesto.monto_final and presupuesto.monto_final > 0:
            nuevo_estado = EstadoPresupuestoEnum.PAGADO_TOTAL
        elif total_pagado > 0:
            nuevo_estado = EstadoPresupuestoEnum.PAGADO_PARCIAL
        elif presupuesto.estado_presupuesto in [
            EstadoPresupuestoEnum.PAGADO_TOTAL,
            EstadoPresupuestoEnum.PAGADO_PARCIAL,
        ]:
            nuevo_estado = EstadoPresupuestoEnum.ACEPTADO
        else:
            return presupuesto

        if presupuesto.estado_presupuesto != nuevo_estado:
            presupuesto.estado_presupuesto = nuevo_estado
            presupuesto.save(update_fields=["estado_presupuesto"])
        return presupuesto
