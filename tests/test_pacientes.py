"""
tests/test_pacientes.py — Tests de creación de pacientes
"""
from django.test import TestCase, Client
from django.urls import reverse
from tests.base import BaseTestCase
from apps.pacientes.models import Paciente
from apps.personas.models import Persona


class PacienteCreacionTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.client.force_login(self.usuario_admin)

    def test_crear_paciente_valido(self):
        """Crear un paciente con datos válidos debe persistir en BD."""
        resp = self.client.post(reverse("pacientes:crear"), {
            "rut": "15.678.901-2",
            "nombres": "Valentina",
            "apellido_paterno": "González",
            "apellido_materno": "",
            "fecha_nacimiento": "1990-05-15",
            "id_sexo": self.sexo.id_sexo,
            "correo": "valentina@test.cl",
            "telefono": "+56912345678",
            "direccion": "",
            "comuna": "",
            "ciudad": "",
            "estado_persona": "activo",
            "contacto_emergencia_nombre": "",
            "contacto_emergencia_telefono": "",
            "observaciones_administrativas": "",
        })
        self.assertEqual(Paciente.objects.filter(
            id_persona__rut="15.678.901-2"
        ).count(), 1)

    def test_crear_paciente_rut_duplicado(self):
        """Un RUT ya existente debe retornar error de formulario."""
        resp = self.client.post(reverse("pacientes:crear"), {
            "rut": "11.222.333-4",  # Ya existe en setUp
            "nombres": "Otro",
            "apellido_paterno": "Nombre",
            "estado_persona": "activo",
            "correo": "nuevo@test.cl",
        })
        # Debe volver al formulario (200) sin crear un duplicado
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Persona.objects.filter(rut="11.222.333-4").count(), 1)

    def test_rut_invalido_rechazado(self):
        """Un RUT con dígito verificador incorrecto debe fallar."""
        resp = self.client.post(reverse("pacientes:crear"), {
            "rut": "11.111.111-1",  # DV incorrecto
            "nombres": "Test",
            "apellido_paterno": "Test",
            "estado_persona": "activo",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "válido")
