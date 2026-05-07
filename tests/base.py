"""
tests/base.py

Clase base con setup compartido para todos los tests.
"""
# --- MONKEYPATCH para compatibilidad con Python 3.14 y Django 5.0 en Tests ---
import django.template.context
def _base_context_copy(self):
    duplicate = self.__class__.__new__(self.__class__)
    duplicate.dicts = self.dicts[:]
    return duplicate
django.template.context.BaseContext.__copy__ = _base_context_copy
# ----------------------------------------------------------------------------

from django.test import TestCase
from django.utils import timezone
from apps.personas.models import Persona, Sexo
from apps.accounts.models import Rol, Usuario, UsuarioRol
from apps.pacientes.models import Paciente
from apps.agenda.models import Box, TipoAtencion, EstadoCita, Cita
from apps.fichas.models import FichaClinica
from apps.odontologos.models import Odontologo
from apps.presupuestos.models import Presupuesto
from apps.pagos.models import MedioPago, Pago
from apps.caja.models import Caja, TipoMovimientoCaja
from apps.tratamientos.models import Tratamiento, PlanTratamiento, PlanTratamientoDetalle


class BaseTestCase(TestCase):

    def setUp(self):
        # Sexo
        self.sexo, _ = Sexo.objects.get_or_create(nombre="masculino")

        # Rol
        self.rol_admin, _ = Rol.objects.get_or_create(nombre="administrador", defaults={"estado_rol": "activo"})
        self.rol_cajero, _ = Rol.objects.get_or_create(nombre="cajero", defaults={"estado_rol": "activo"})

        # Persona + Usuario administrador
        self.persona_admin, _ = Persona.objects.get_or_create(
            rut="12.345.678-9",
            defaults={
                "nombres": "Admin",
                "apellido_paterno": "Test",
                "id_sexo": self.sexo,
            }
        )
        self.usuario_admin, _ = Usuario.objects.get_or_create(
            username="admin_test",
            defaults={
                "id_persona": self.persona_admin,
                "estado_acceso": "activo",
                "is_staff": True,
                "is_superuser": True,
            }
        )
        self.usuario_admin.set_password("Admin1234!")
        self.usuario_admin.save()
        UsuarioRol.objects.get_or_create(id_usuario=self.usuario_admin, rol=self.rol_admin)

        # Persona + Usuario odontólogo
        self.persona_od, _ = Persona.objects.get_or_create(
            rut="98.765.432-1",
            defaults={
                "nombres": "Carlos",
                "apellido_paterno": "Soto",
                "id_sexo": self.sexo,
            }
        )
        self.usuario_od, _ = Usuario.objects.get_or_create(
            username="carlos_soto",
            defaults={
                "id_persona": self.persona_od,
                "estado_acceso": "activo",
            }
        )
        self.usuario_od.set_password("Odont1234!")
        self.usuario_od.save()

        self.odontologo, _ = Odontologo.objects.get_or_create(
            id_usuario=self.usuario_od,
            defaults={
                "numero_registro": "REG-001",
                "duracion_cita_base_min": 30,
                "estado_profesional": "activo",
            }
        )

        # Box
        self.box, _ = Box.objects.get_or_create(nombre="Box 1", defaults={"estado_box": "activo"})

        # Estado de cita
        self.estado_pendiente, _ = EstadoCita.objects.get_or_create(nombre="pendiente")
        self.estado_confirmada, _ = EstadoCita.objects.get_or_create(nombre="confirmada")
        self.estado_cancelada, _ = EstadoCita.objects.get_or_create(nombre="cancelada")
        self.estado_atendida, _ = EstadoCita.objects.get_or_create(nombre="atendida")

        # Tipo de atención
        self.tipo_atencion, _ = TipoAtencion.objects.get_or_create(
            nombre="evaluacion",
            defaults={
                "duracion_estimada_min": 30,
                "estado_tipo_atencion": "activo",
            }
        )

        # Paciente
        self.persona_paciente, _ = Persona.objects.get_or_create(
            rut="11.222.333-4",
            defaults={
                "nombres": "María",
                "apellido_paterno": "Pérez",
                "id_sexo": self.sexo,
            }
        )
        self.paciente, _ = Paciente.objects.get_or_create(id_persona=self.persona_paciente)

        # Ficha
        self.ficha, _ = FichaClinica.objects.get_or_create(
            id_paciente=self.paciente,
            defaults={
                "numero_ficha": "FC-000001",
                "fecha_apertura": timezone.localdate(),
                "estado_ficha": "activa",
            }
        )

        # Tratamiento
        self.tratamiento, _ = Tratamiento.objects.get_or_create(
            codigo="TRAT-001",
            defaults={
                "nombre": "Limpieza dental",
                "valor_referencial": 25000,
                "estado_tratamiento": "activo",
            }
        )

        # Medio de pago
        self.medio_pago, _ = MedioPago.objects.get_or_create(nombre="efectivo", defaults={"estado_medio_pago": "activo"})

        # Tipo movimiento caja
        self.tipo_ingreso, _ = TipoMovimientoCaja.objects.get_or_create(nombre="ingreso")
        self.tipo_egreso, _ = TipoMovimientoCaja.objects.get_or_create(nombre="egreso")

    def crear_cita(self, inicio=None, fin=None, odontologo=None, box=None, estado=None):
        inicio = inicio or timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        fin = fin or inicio.replace(hour=10, minute=30)
        return Cita.objects.create(
            id_paciente=self.paciente,
            id_odontologo=odontologo or self.odontologo,
            id_box=box or self.box,
            id_tipo_atencion=self.tipo_atencion,
            id_estado_cita=estado or self.estado_pendiente,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=fin,
            id_usuario_registra=self.usuario_admin,
        )
