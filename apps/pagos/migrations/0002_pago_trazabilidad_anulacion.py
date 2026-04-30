# Generated manually for Fase 8 payment traceability.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("pagos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pago",
            name="observacion",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="pago",
            name="fecha_anulacion",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="pago",
            name="id_usuario_anula",
            field=models.ForeignKey(
                blank=True,
                db_column="id_usuario_anula",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="pagos_anulados",
                to="accounts.usuario",
            ),
        ),
        migrations.AddField(
            model_name="pago",
            name="motivo_anulacion",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
