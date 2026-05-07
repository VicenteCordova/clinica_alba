import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.pagos.models import MedioPago

medios = [
    {"nombre": "Efectivo", "descripcion": "Pago en dinero en efectivo"},
    {"nombre": "Tarjeta de Crédito", "descripcion": "Pago mediante tarjeta de crédito"},
    {"nombre": "Tarjeta de Débito", "descripcion": "Pago mediante tarjeta de débito"},
    {"nombre": "Transferencia Bancaria", "descripcion": "Transferencia electrónica directa"},
    {"nombre": "Cheque", "descripcion": "Documento de pago"},
]

for m in medios:
    MedioPago.objects.get_or_create(nombre=m["nombre"], defaults={"descripcion": m["descripcion"]})

print("Medios de pago creados exitosamente.")
