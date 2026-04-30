# Generated manually for Fase 5 clinical attention fields.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fichas", "0002_evolucionclinica_idx_evoluciones_cita_and_more"),
        ("odontologos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="evolucionclinica",
            name="id_ficha_clinica",
            field=models.ForeignKey(
                blank=True,
                db_column="id_ficha_clinica",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="evoluciones",
                to="fichas.fichaclinica",
            ),
        ),
        migrations.AddField(
            model_name="evolucionclinica",
            name="id_odontologo",
            field=models.ForeignKey(
                blank=True,
                db_column="id_odontologo",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="evoluciones_clinicas",
                to="odontologos.odontologo",
            ),
        ),
        migrations.AddField(
            model_name="evolucionclinica",
            name="motivo_consulta",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="evolucionclinica",
            name="procedimiento_realizado",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="evolucionclinica",
            name="tratamiento_sugerido",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="evolucionclinica",
            name="proxima_accion",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="evolucionclinica",
            name="fecha_actualizacion",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
