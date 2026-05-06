# Generated manually for role/permission hardening.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("imagenologia", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="archivoexamenimagenologico",
            name="estado",
            field=models.CharField(
                choices=[
                    ("activo", "Activo"),
                    ("anulado", "Anulado"),
                    ("reemplazado", "Reemplazado"),
                ],
                default="activo",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="archivoexamenimagenologico",
            name="motivo_anulacion",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="archivoexamenimagenologico",
            name="fecha_anulacion",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="archivoexamenimagenologico",
            name="usuario_responsable",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="archivos_imagenologia_gestionados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="archivoexamenimagenologico",
            name="adjunto_reemplazo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="adjuntos_reemplazados",
                to="imagenologia.archivoexamenimagenologico",
            ),
        ),
    ]
