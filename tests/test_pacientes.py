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
            "persona-rut": "12.345.678-5",
            "persona-nombres": "Valentina",
            "persona-apellido_paterno": "González",
            "persona-apellido_materno": "Pérez",
            "persona-fecha_nacimiento": "1990-05-15",
            "persona-id_sexo": self.sexo.id_sexo,
            "persona-correo": "valentina@test.cl",
            "persona-telefono": "+56912345678",
            "persona-direccion": "Calle 1",
            "persona-comuna": "Santiago",
            "persona-ciudad": "Santiago",
            "persona-estado_persona": "activo",
            "paciente-contacto_emergencia_nombre": "",
            "paciente-contacto_emergencia_telefono": "",
            "paciente-observaciones_administrativas": "",
        })
        self.assertEqual(Paciente.objects.filter(
            id_persona__rut="12.345.678-5"
        ).count(), 1)

    def test_crear_paciente_rut_duplicado(self):
        """Un RUT ya existente debe retornar error de formulario."""
        resp = self.client.post(reverse("pacientes:crear"), {
            "persona-rut": "11.222.333-4",  # Ya existe en setUp
            "persona-nombres": "Otro",
            "persona-apellido_paterno": "Nombre",
            "persona-apellido_materno": "Apellido",
            "persona-fecha_nacimiento": "1990-05-15",
            "persona-id_sexo": self.sexo.id_sexo,
            "persona-direccion": "Calle 1",
            "persona-comuna": "Santiago",
            "persona-ciudad": "Santiago",
            "persona-estado_persona": "activo",
            "persona-correo": "nuevo@test.cl",
        })
        # Debe volver al formulario (200) sin crear un duplicado
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Persona.objects.filter(rut="11.222.333-4").count(), 1)

    def test_rut_invalido_rechazado(self):
        """Un RUT con dígito verificador incorrecto debe fallar."""
        resp = self.client.post(reverse("pacientes:crear"), {
            "persona-rut": "12.345.678-9",  # DV incorrecto
            "persona-nombres": "Test",
            "persona-apellido_paterno": "Test",
            "persona-apellido_materno": "Test",
            "persona-fecha_nacimiento": "1990-05-15",
            "persona-id_sexo": self.sexo.id_sexo,
            "persona-direccion": "Calle 1",
            "persona-comuna": "Santiago",
            "persona-ciudad": "Santiago",
            "persona-estado_persona": "activo",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "lido")
