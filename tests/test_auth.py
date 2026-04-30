"""
tests/test_auth.py — Tests de autenticación
"""
from django.test import TestCase, Client
from django.urls import reverse
from tests.base import BaseTestCase


class LoginTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.url_login = reverse("accounts:login")

    def test_login_correcto(self):
        """Un usuario activo puede iniciar sesión con credenciales correctas."""
        resp = self.client.post(self.url_login, {
            "username": "admin_test",
            "password": "Admin1234!",
        })
        self.assertRedirects(resp, reverse("dashboard:index"))
        self.assertTrue(resp.wsgi_request.user.is_authenticated)

    def test_login_password_incorrecta(self):
        """Credenciales incorrectas no autentican al usuario."""
        resp = self.client.post(self.url_login, {
            "username": "admin_test",
            "password": "WrongPassword",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    def test_login_usuario_bloqueado(self):
        """Un usuario bloqueado no puede iniciar sesión."""
        self.usuario_admin.estado_acceso = "bloqueado"
        self.usuario_admin.save()
        resp = self.client.post(self.url_login, {
            "username": "admin_test",
            "password": "Admin1234!",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    def test_logout(self):
        """El usuario puede cerrar sesión."""
        self.client.force_login(self.usuario_admin)
        resp = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(resp, self.url_login)

    def test_redireccion_sin_login(self):
        """Las páginas protegidas redirigen al login si no hay sesión."""
        resp = self.client.get(reverse("dashboard:index"))
        self.assertRedirects(resp, f"{self.url_login}?next=/")
