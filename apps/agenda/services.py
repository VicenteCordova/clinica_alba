"""
apps/agenda/services.py

CitaService: lógica de negocio para crear, editar y cambiar estado de citas.

Regla de solapamiento (RN-01 actualizada):
  Solo bloquean el slot: pendiente, confirmada, atendida.
  cancelada y reprogramada LIBERAN el slot.
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

# Estados que bloquean el slot horario
ESTADOS_QUE_BLOQUEAN = ["pendiente", "confirmada", "atendida"]


class CitaService:

    @staticmethod
    def verificar_solapamiento(
        id_odontologo: int,
        id_box: int,
        fecha_hora_inicio,
        fecha_hora_fin,
        excluir_cita_id: int = None,
    ):
        """
        Verifica que no haya solapamiento de horario para el odontólogo ni para el box.
        Solo considera citas en estados que bloquean el slot.

        Raises ValidationError si hay conflicto.
        """
        from apps.agenda.models import Cita

        qs_base = Cita.objects.filter(
            id_estado_cita__nombre__in=ESTADOS_QUE_BLOQUEAN,
            fecha_hora_inicio__lt=fecha_hora_fin,
            fecha_hora_fin__gt=fecha_hora_inicio,
        )
        if excluir_cita_id:
            qs_base = qs_base.exclude(id_cita=excluir_cita_id)

        # Solapamiento de odontólogo
        if qs_base.filter(id_odontologo_id=id_odontologo).exists():
            raise ValidationError(
                "El odontólogo ya tiene una cita agendada en ese horario."
            )

        # Solapamiento de box
        if qs_base.filter(id_box_id=id_box).exists():
            raise ValidationError(
                "El box ya está ocupado en ese horario."
            )

    @staticmethod
    @transaction.atomic
    def crear_cita(datos: dict, usuario) -> "Cita":
        """
        Crea una cita validando solapamiento primero.
        Registra el estado inicial en historial.
        """
        from apps.agenda.models import Cita, HistorialCita
        from apps.auditoria.models import Bitacora

        CitaService.verificar_solapamiento(
            id_odontologo=datos["id_odontologo"].id_odontologo,
            id_box=datos["id_box"].id_box,
            fecha_hora_inicio=datos["fecha_hora_inicio"],
            fecha_hora_fin=datos["fecha_hora_fin"],
        )

        cita = Cita(
            id_paciente=datos["id_paciente"],
            id_odontologo=datos["id_odontologo"],
            id_box=datos["id_box"],
            id_tipo_atencion=datos["id_tipo_atencion"],
            id_estado_cita=datos["id_estado_cita"],
            fecha_hora_inicio=datos["fecha_hora_inicio"],
            fecha_hora_fin=datos["fecha_hora_fin"],
            motivo_consulta=datos.get("motivo_consulta"),
            observaciones=datos.get("observaciones"),
            id_usuario_registra=usuario,
        )
        cita.full_clean()
        cita.save()

        # Registrar en historial (sin estado anterior)
        HistorialCita.objects.create(
            id_cita=cita,
            id_estado_anterior=None,
            id_estado_nuevo=cita.id_estado_cita,
            motivo_cambio="Cita creada",
            id_usuario_responsable=usuario,
        )

        Bitacora.registrar(
            usuario=usuario,
            modulo="agenda",
            accion="creacion",
            tabla_afectada="citas",
            id_registro_afectado=cita.id_cita,
            descripcion=f"Cita creada para {cita.id_paciente.nombre_completo}",
        )

        return cita

    @staticmethod
    @transaction.atomic
    def editar_cita(cita, datos: dict, usuario) -> "Cita":
        """Edita una cita verificando solapamiento excluyendo la cita actual."""
        CitaService.verificar_solapamiento(
            id_odontologo=datos["id_odontologo"].id_odontologo,
            id_box=datos["id_box"].id_box,
            fecha_hora_inicio=datos["fecha_hora_inicio"],
            fecha_hora_fin=datos["fecha_hora_fin"],
            excluir_cita_id=cita.id_cita,
        )

        for campo, valor in datos.items():
            setattr(cita, campo, valor)
        cita.full_clean()
        cita.save()

        from apps.auditoria.models import Bitacora
        Bitacora.registrar(
            usuario=usuario,
            modulo="agenda",
            accion="edicion",
            tabla_afectada="citas",
            id_registro_afectado=cita.id_cita,
            descripcion=f"Cita #{cita.id_cita} editada",
        )

        return cita

    @staticmethod
    @transaction.atomic
    def cambiar_estado(
        cita,
        nuevo_estado,
        usuario,
        motivo: str = None,
    ) -> "Cita":
        """
        Cambia el estado de una cita y lo registra en el historial.
        Valida que el estado nuevo sea distinto del actual.
        """
        from apps.agenda.models import HistorialCita
        from apps.auditoria.models import Bitacora

        if cita.id_estado_cita == nuevo_estado:
            raise ValidationError("El nuevo estado debe ser diferente al estado actual.")

        estado_anterior = cita.id_estado_cita
        cita.id_estado_cita = nuevo_estado
        cita.save(update_fields=["id_estado_cita", "fecha_actualizacion"])

        HistorialCita.objects.create(
            id_cita=cita,
            id_estado_anterior=estado_anterior,
            id_estado_nuevo=nuevo_estado,
            motivo_cambio=motivo,
            id_usuario_responsable=usuario,
        )

        Bitacora.registrar(
            usuario=usuario,
            modulo="agenda",
            accion="cambio_estado",
            tabla_afectada="citas",
            id_registro_afectado=cita.id_cita,
            descripcion=(
                f"Cita #{cita.id_cita}: "
                f"{estado_anterior.nombre} → {nuevo_estado.nombre}"
            ),
        )

        return cita
