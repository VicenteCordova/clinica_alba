# Generated manually for Fase 7 treatment plan states.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tratamientos", "0002_plan_contexto_clinico"),
    ]

    operations = [
        migrations.AlterField(
            model_name="plantratamiento",
            name="estado_plan",
            field=models.CharField(
                choices=[
                    ("activo", "Activo"),
                    ("cerrado", "Cerrado"),
                    ("anulado", "Anulado"),
                    ("borrador", "Borrador"),
                    ("propuesto", "Propuesto"),
                    ("aceptado_parcial", "Aceptado parcialmente"),
                    ("aceptado", "Aceptado"),
                    ("rechazado", "Rechazado"),
                    ("en_curso", "En curso"),
                    ("suspendido", "Suspendido"),
                    ("finalizado", "Finalizado"),
                ],
                default="activo",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="plantratamientodetalle",
            name="estado_detalle",
            field=models.CharField(
                choices=[
                    ("pendiente", "Pendiente"),
                    ("aprobado", "Aprobado"),
                    ("en_curso", "En curso"),
                    ("realizado", "Realizado"),
                    ("suspendido", "Suspendido"),
                    ("rechazado", "Rechazado"),
                    ("anulado", "Anulado"),
                ],
                default="pendiente",
                max_length=20,
            ),
        ),
    ]
