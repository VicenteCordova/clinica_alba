"""
tests/test_pagos.py — Tests de validación de sobrepago y caja
"""
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from tests.base import BaseTestCase
from apps.presupuestos.models import Presupuesto
from apps.tratamientos.models import PlanTratamiento, PlanTratamientoDetalle
from apps.pagos.services import PagoService
from apps.caja.services import CajaService


class SobrepagoTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.plan = PlanTratamiento.objects.create(
            id_ficha_clinica=self.ficha,
            id_odontologo=self.odontologo,
        )
        self.presupuesto = Presupuesto.objects.create(
            id_plan_tratamiento=self.plan,
            numero_presupuesto="PRES-000001",
            monto_bruto=Decimal("50000"),
            descuento_total=Decimal("0"),
            monto_final=Decimal("50000"),
            id_usuario_emite=self.usuario_admin,
        )

    def test_pago_valido(self):
        """Un pago dentro del monto permitido debe crearse correctamente."""
        pago = PagoService.registrar_pago(
            datos={
                "id_presupuesto": self.presupuesto,
                "id_medio_pago": self.medio_pago,
                "monto": Decimal("30000"),
                "estado_pago": "vigente",
            },
            usuario=self.usuario_admin,
        )
        self.assertEqual(pago.estado_pago, "vigente")
        self.assertEqual(pago.monto, Decimal("30000"))

    def test_sobrepago_rechazado(self):
        """Un pago que supera el monto final del presupuesto debe ser rechazado."""
        with self.assertRaises(ValidationError):
            PagoService.registrar_pago(
                datos={
                    "id_presupuesto": self.presupuesto,
                    "id_medio_pago": self.medio_pago,
                    "monto": Decimal("60000"),  # supera 50000
                    "estado_pago": "vigente",
                },
                usuario=self.usuario_admin,
            )

    def test_pago_anulado_no_suma(self):
        """Un pago anulado no cuenta para el límite de sobrepago."""
        PagoService.registrar_pago(
            datos={
                "id_presupuesto": self.presupuesto,
                "id_medio_pago": self.medio_pago,
                "monto": Decimal("40000"),
                "estado_pago": "vigente",
            },
            usuario=self.usuario_admin,
        )
        # Anular el pago
        from apps.pagos.models import Pago
        pago = Pago.objects.get(id_presupuesto=self.presupuesto)
        PagoService.anular_pago(pago=pago, usuario=self.usuario_admin)

        # Ahora se puede pagar el total nuevamente
        pago2 = PagoService.registrar_pago(
            datos={
                "id_presupuesto": self.presupuesto,
                "id_medio_pago": self.medio_pago,
                "monto": Decimal("50000"),
                "estado_pago": "vigente",
            },
            usuario=self.usuario_admin,
        )
        self.assertEqual(pago2.monto, Decimal("50000"))


class CajaTest(BaseTestCase):

    def test_abrir_caja(self):
        """Un usuario puede abrir una caja con monto inicial."""
        caja = CajaService.abrir_caja(
            usuario=self.usuario_admin,
            monto_inicial=Decimal("50000"),
        )
        self.assertEqual(caja.estado_caja, "abierta")
        self.assertEqual(caja.monto_inicial, Decimal("50000"))

    def test_caja_duplicada_rechazada(self):
        """Un usuario no puede abrir dos cajas simultáneamente."""
        CajaService.abrir_caja(
            usuario=self.usuario_admin,
            monto_inicial=Decimal("10000"),
        )
        with self.assertRaises(ValidationError):
            CajaService.abrir_caja(
                usuario=self.usuario_admin,
                monto_inicial=Decimal("20000"),
            )

    def test_cerrar_caja(self):
        """Una caja abierta puede cerrarse con monto final."""
        caja = CajaService.abrir_caja(
            usuario=self.usuario_admin,
            monto_inicial=Decimal("10000"),
        )
        caja = CajaService.cerrar_caja(
            caja=caja,
            usuario_cierre=self.usuario_admin,
            monto_final=Decimal("12000"),
        )
        self.assertEqual(caja.estado_caja, "cerrada")
        self.assertIsNotNone(caja.fecha_cierre)
