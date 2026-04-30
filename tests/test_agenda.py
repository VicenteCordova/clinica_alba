"""
tests/test_agenda.py — Tests de solapamiento de citas
"""
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from tests.base import BaseTestCase
from apps.agenda.services import CitaService
from apps.agenda.models import EstadoCita


class SolapamientoCitasTest(BaseTestCase):

    def test_no_solapamiento_mismo_horario_bloquea(self):
        """
        Dos citas en el mismo horario para el mismo odontólogo deben fallar.
        La primera cita 'pendiente' bloquea el slot.
        """
        inicio = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        fin = inicio.replace(hour=9, minute=30)
        self.crear_cita(inicio=inicio, fin=fin)

        with self.assertRaises(ValidationError):
            CitaService.verificar_solapamiento(
                id_odontologo=self.odontologo.id_odontologo,
                id_box=self.box.id_box,
                fecha_hora_inicio=inicio,
                fecha_hora_fin=fin,
            )

    def test_cancelada_libera_slot(self):
        """
        Una cita cancelada NO debe bloquear el horario para nuevas citas.
        """
        inicio = timezone.now().replace(hour=11, minute=0, second=0, microsecond=0)
        fin = inicio.replace(hour=11, minute=30)
        cita_cancelada = self.crear_cita(inicio=inicio, fin=fin, estado=self.estado_cancelada)

        # Debe pasar sin excepción
        CitaService.verificar_solapamiento(
            id_odontologo=self.odontologo.id_odontologo,
            id_box=self.box.id_box,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=fin,
        )

    def test_solapamiento_box_bloqueado(self):
        """
        Si el box está ocupado con una cita confirmada,
        otra cita no puede usar el mismo box.
        """
        inicio = timezone.now().replace(hour=14, minute=0, second=0, microsecond=0)
        fin = inicio.replace(hour=14, minute=30)
        self.crear_cita(inicio=inicio, fin=fin, estado=self.estado_confirmada)

        # Crear otro odontólogo para que no sea solapamiento del mismo od
        from apps.personas.models import Persona
        from apps.accounts.models import Usuario
        from apps.odontologos.models import Odontologo

        p2 = Persona.objects.create(rut="55.555.555-5", nombres="Pedro", apellido_paterno="López", id_sexo=self.sexo)
        u2 = Usuario.objects.create(id_persona=p2, username="pedro_l", estado_acceso="activo")
        u2.set_password("Test1234!")
        u2.save()
        od2 = Odontologo.objects.create(id_usuario=u2, numero_registro="REG-002", duracion_cita_base_min=30)

        with self.assertRaises(ValidationError):
            CitaService.verificar_solapamiento(
                id_odontologo=od2.id_odontologo,
                id_box=self.box.id_box,
                fecha_hora_inicio=inicio,
                fecha_hora_fin=fin,
            )
