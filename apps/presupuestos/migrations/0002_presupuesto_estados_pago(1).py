# Generated manually for Fase 8 payment states.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("presupuestos", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="presupuesto",
            name="estado_presupuesto",
            field=models.CharField(
                choices=[
                    ("vigente", "Vigente"),
                    ("vencido", "Vencido"),
                    ("aceptado", "Aceptado"),
                    ("rechazado", "Rechazado"),
                    ("anulado", "Anulado"),
                    ("pagado_parcial", "Pagado parcial"),
                    ("pagado_total", "Pagado total"),
                ],
                default="vigente",
                max_length=20,
            ),
        ),
    ]
