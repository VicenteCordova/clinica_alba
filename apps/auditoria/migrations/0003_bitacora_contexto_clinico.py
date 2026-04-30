# Generated manually for Fase 9-compatible audit context.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agenda", "0002_cita_idx_citas_estado_cita_idx_citas_fecha"),
        ("auditoria", "0002_bitacora_idx_bitacora_usr_fecha"),
        ("pacientes", "0002_paciente_idx_pacientes_persona"),
    ]

    operations = [
        migrations.AddField(
            model_name="bitacora",
            name="rol_usuario",
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name="bitacora",
            name="objeto_afectado",
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name="bitacora",
            name="paciente",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="eventos_auditoria",
                to="pacientes.paciente",
            ),
        ),
        migrations.AddField(
            model_name="bitacora",
            name="cita",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="eventos_auditoria",
                to="agenda.cita",
            ),
        ),
        migrations.AddField(
            model_name="bitacora",
            name="user_agent",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="bitacora",
            name="datos_anteriores",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="bitacora",
            name="datos_nuevos",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="bitacora",
            index=models.Index(fields=["paciente", "fecha_evento"], name="idx_bitacora_paciente_fecha"),
        ),
        migrations.AddIndex(
            model_name="bitacora",
            index=models.Index(fields=["cita", "fecha_evento"], name="idx_bitacora_cita_fecha"),
        ),
    ]
