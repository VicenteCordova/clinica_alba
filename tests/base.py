"""
tests/base.py

Clase base con setup compartido para todos los tests.
"""
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
        self.sexo = Sexo.objects.create(nombre="masculino")

        # Rol
        self.rol_admin = Rol.objects.create(nombre="administrador", estado_rol="activo")
        self.rol_cajero = Rol.objects.create(nombre="cajero", estado_rol="activo")

        # Persona + Usuario administrador
        self.persona_admin = Persona.objects.create(
            rut="12.345.678-9",
            nombres="Admin",
            apellido_paterno="Test",
            id_sexo=self.sexo,
        )
        self.usuario_admin = Usuario.objects.create(
            id_persona=self.persona_admin,
            username="admin_test",
            estado_acceso="activo",
            is_staff=True,
            is_superuser=True,
        )
        self.usuario_admin.set_password("Admin1234!")
        self.usuario_admin.save()
        UsuarioRol.objects.create(id_usuario=self.usuario_admin, rol=self.rol_admin)

        # Persona + Usuario odontólogo
        self.persona_od = Persona.objects.create(
            rut="98.765.432-1",
            nombres="Carlos",
            apellido_paterno="Soto",
            id_sexo=self.sexo,
        )
        self.usuario_od = Usuario.objects.create(
            id_persona=self.persona_od,
            username="carlos_soto",
            estado_acceso="activo",
        )
        self.usuario_od.set_password("Odont1234!")
        self.usuario_od.save()

        self.odontologo = Odontologo.objects.create(
            id_usuario=self.usuario_od,
            numero_registro="REG-001",
            duracion_cita_base_min=30,
            estado_profesional="activo",
        )

        # Box
        self.box = Box.objects.create(nombre="Box 1", estado_box="activo")

        # Estado de cita
        self.estado_pendiente = EstadoCita.objects.create(nombre="pendiente")
        self.estado_confirmada = EstadoCita.objects.create(nombre="confirmada")
        self.estado_cancelada = EstadoCita.objects.create(nombre="cancelada")
        self.estado_atendida = EstadoCita.objects.create(nombre="atendida")

        # Tipo de atención
        self.tipo_atencion = TipoAtencion.objects.create(
            nombre="evaluacion",
            duracion_estimada_min=30,
            estado_tipo_atencion="activo",
        )

        # Paciente
        self.persona_paciente = Persona.objects.create(
            rut="11.222.333-4",
            nombres="María",
            apellido_paterno="Pérez",
            id_sexo=self.sexo,
        )
        self.paciente = Paciente.objects.create(id_persona=self.persona_paciente)

        # Ficha
        self.ficha = FichaClinica.objects.create(
            id_paciente=self.paciente,
            numero_ficha="FC-000001",
            fecha_apertura=timezone.localdate(),
            estado_ficha="activa",
        )

        # Tratamiento
        self.tratamiento = Tratamiento.objects.create(
            codigo="TRAT-001",
            nombre="Limpieza dental",
            valor_referencial=25000,
            estado_tratamiento="activo",
        )

        # Medio de pago
        self.medio_pago = MedioPago.objects.create(nombre="efectivo", estado_medio_pago="activo")

        # Tipo movimiento caja
        self.tipo_ingreso = TipoMovimientoCaja.objects.create(nombre="ingreso")
        self.tipo_egreso = TipoMovimientoCaja.objects.create(nombre="egreso")

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
