"""
apps/core/transitions.py

Servicio centralizado de transiciones de estado.
Cada modelo con estados define sus transiciones válidas aquí.
"""
from django.core.exceptions import ValidationError
from apps.auditoria.models import Bitacora
from apps.core.enums import (
    EstadoPlanEnum,
    EstadoDetallePlanEnum,
    EstadoPresupuestoEnum,
    EstadoPagoEnum,
    EstadoFichaEnum,
)

# ── Matrices de transición ──────────────────────────────────────────────

TRANSICIONES_PLAN = {
    EstadoPlanEnum.ACTIVO: [
        EstadoPlanEnum.EN_CURSO,
        EstadoPlanEnum.ANULADO,
    ],
    EstadoPlanEnum.BORRADOR: [
        EstadoPlanEnum.PROPUESTO,
        EstadoPlanEnum.ANULADO,
    ],
    EstadoPlanEnum.PROPUESTO: [
        EstadoPlanEnum.ACEPTADO,
        EstadoPlanEnum.ACEPTADO_PARCIAL,
        EstadoPlanEnum.RECHAZADO,
    ],
    EstadoPlanEnum.ACEPTADO: [
        EstadoPlanEnum.EN_CURSO,
        EstadoPlanEnum.ANULADO,
    ],
    EstadoPlanEnum.ACEPTADO_PARCIAL: [
        EstadoPlanEnum.EN_CURSO,
        EstadoPlanEnum.ANULADO,
    ],
    EstadoPlanEnum.EN_CURSO: [
        EstadoPlanEnum.SUSPENDIDO,
        EstadoPlanEnum.FINALIZADO,
        EstadoPlanEnum.ANULADO,
    ],
    EstadoPlanEnum.SUSPENDIDO: [
        EstadoPlanEnum.EN_CURSO,
        EstadoPlanEnum.ANULADO,
    ],
    EstadoPlanEnum.RECHAZADO: [],
    EstadoPlanEnum.FINALIZADO: [],
    EstadoPlanEnum.ANULADO: [],
    EstadoPlanEnum.CERRADO: [],
}

TRANSICIONES_DETALLE_PLAN = {
    EstadoDetallePlanEnum.PENDIENTE: [
        EstadoDetallePlanEnum.APROBADO,
        EstadoDetallePlanEnum.RECHAZADO,
        EstadoDetallePlanEnum.ANULADO,
    ],
    EstadoDetallePlanEnum.APROBADO: [
        EstadoDetallePlanEnum.EN_CURSO,
        EstadoDetallePlanEnum.ANULADO,
    ],
    EstadoDetallePlanEnum.EN_CURSO: [
        EstadoDetallePlanEnum.REALIZADO,
        EstadoDetallePlanEnum.SUSPENDIDO,
        EstadoDetallePlanEnum.ANULADO,
    ],
    EstadoDetallePlanEnum.SUSPENDIDO: [
        EstadoDetallePlanEnum.EN_CURSO,
        EstadoDetallePlanEnum.ANULADO,
    ],
    EstadoDetallePlanEnum.REALIZADO: [],
    EstadoDetallePlanEnum.RECHAZADO: [],
    EstadoDetallePlanEnum.ANULADO: [],
}

TRANSICIONES_PRESUPUESTO = {
    EstadoPresupuestoEnum.VIGENTE: [
        EstadoPresupuestoEnum.ACEPTADO,
        EstadoPresupuestoEnum.RECHAZADO,
        EstadoPresupuestoEnum.VENCIDO,
        EstadoPresupuestoEnum.ANULADO,
    ],
    EstadoPresupuestoEnum.ACEPTADO: [
        EstadoPresupuestoEnum.PAGADO_PARCIAL,
        EstadoPresupuestoEnum.PAGADO_TOTAL,
        EstadoPresupuestoEnum.ANULADO,
    ],
    EstadoPresupuestoEnum.PAGADO_PARCIAL: [
        EstadoPresupuestoEnum.PAGADO_TOTAL,
        EstadoPresupuestoEnum.ACEPTADO,
        EstadoPresupuestoEnum.ANULADO,
    ],
    EstadoPresupuestoEnum.PAGADO_TOTAL: [],
    EstadoPresupuestoEnum.VENCIDO: [
        EstadoPresupuestoEnum.ANULADO,
    ],
    EstadoPresupuestoEnum.RECHAZADO: [
        EstadoPresupuestoEnum.ANULADO,
    ],
    EstadoPresupuestoEnum.ANULADO: [],
}

TRANSICIONES_FICHA = {
    EstadoFichaEnum.ACTIVA: [
        EstadoFichaEnum.CERRADA,
        EstadoFichaEnum.BLOQUEADA,
    ],
    EstadoFichaEnum.CERRADA: [
        EstadoFichaEnum.ACTIVA,
    ],
    EstadoFichaEnum.BLOQUEADA: [],
}


# ── Servicio de transiciones ────────────────────────────────────────────

def cambiar_estado(instancia, campo_estado, nuevo_estado, mapa_transiciones,
                   usuario=None, motivo=None, modulo=None, request=None):
    """
    Cambia el estado de una instancia de modelo, validando contra la
    matriz de transiciones permitidas.

    Args:
        instancia: Instancia del modelo Django.
        campo_estado: Nombre del campo de estado (str), ej: 'estado_plan'.
        nuevo_estado: Valor del nuevo estado (enum member).
        mapa_transiciones: Dict con las transiciones válidas.
        usuario: Usuario que realiza la acción (para auditoría).
        motivo: Motivo del cambio (opcional).
        modulo: Nombre del módulo para la bitácora.
        request: HttpRequest (para IP de auditoría).

    Returns:
        La instancia actualizada.

    Raises:
        ValidationError si la transición no es válida.
    """
    estado_actual = getattr(instancia, campo_estado)
    destinos_validos = mapa_transiciones.get(estado_actual, [])

    if nuevo_estado not in destinos_validos:
        raise ValidationError(
            f"Transición no permitida: '{estado_actual}' → '{nuevo_estado}'. "
            f"Destinos válidos: {[str(d) for d in destinos_validos]}"
        )

    setattr(instancia, campo_estado, nuevo_estado)
    instancia.save(update_fields=[campo_estado])

    # Registrar en bitácora si hay usuario
    if usuario and modulo:
        tabla = instancia._meta.db_table
        pk_field = instancia._meta.pk.name
        pk_value = getattr(instancia, pk_field)
        Bitacora.registrar(
            usuario=usuario,
            modulo=modulo,
            accion="cambio_estado",
            tabla_afectada=tabla,
            id_registro_afectado=pk_value,
            descripcion=(
                f"Estado cambiado: {estado_actual} → {nuevo_estado}"
                + (f". Motivo: {motivo}" if motivo else "")
            ),
            request=request,
        )

    return instancia
