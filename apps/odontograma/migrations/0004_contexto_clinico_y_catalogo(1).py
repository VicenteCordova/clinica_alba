# Generated manually for odontogram clinical integrity hardening.

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


CARAS = [
    "oclusal",
    "incisal",
    "vestibular",
    "palatina",
    "lingual",
    "mesial",
    "distal",
]


CONDICIONES = [
    ("sano", "Diente o superficie sin hallazgos patologicos"),
    ("caries", "Lesion cariosa activa o sospecha clinica"),
    ("restauracion", "Restauracion, obturacion, resina o amalgama"),
    ("obturacion", "Alias historico de restauracion"),
    ("ausente", "Pieza dental ausente"),
    ("extraccion_indicada", "Pieza con extraccion indicada"),
    ("extraccion", "Extraccion indicada o realizada"),
    ("endodoncia", "Tratamiento endodontico realizado o indicado"),
    ("corona", "Corona protesica instalada o indicada"),
    ("implante", "Implante dental instalado"),
    ("fractura", "Fractura dental"),
    ("movilidad", "Movilidad dentaria relevante"),
    ("observacion", "Hallazgo u observacion clinica no clasificada"),
]


def seed_catalogo_odontograma(apps, schema_editor):
    CaraDental = apps.get_model("odontograma", "CaraDental")
    CondicionOdontologica = apps.get_model("odontograma", "CondicionOdontologica")

    for nombre in CARAS:
        CaraDental.objects.get_or_create(nombre=nombre)

    for nombre, descripcion in CONDICIONES:
        CondicionOdontologica.objects.update_or_create(
            nombre=nombre,
            defaults={"descripcion": descripcion, "estado_condicion": "activo"},
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("agenda", "0002_cita_idx_citas_estado_cita_idx_citas_fecha"),
        ("fichas", "0003_evolucionclinica_campos_atencion"),
        ("odontograma", "0003_odontograma_idx_odontogramas_ficha"),
        ("odontologos", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="odontograma",
            name="id_evolucion",
            field=models.ForeignKey(
                blank=True,
                db_column="id_evolucion",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="odontogramas",
                to="fichas.evolucionclinica",
            ),
        ),
        migrations.AddField(
            model_name="odontograma",
            name="id_odontologo",
            field=models.ForeignKey(
                blank=True,
                db_column="id_odontologo",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="odontogramas",
                to="odontologos.odontologo",
            ),
        ),
        migrations.AddField(
            model_name="odontograma",
            name="id_usuario_crea",
            field=models.ForeignKey(
                blank=True,
                db_column="id_usuario_crea",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="odontogramas_creados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="odontograma",
            name="id_usuario_actualiza",
            field=models.ForeignKey(
                blank=True,
                db_column="id_usuario_actualiza",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="odontogramas_actualizados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="odontograma",
            name="fecha_actualizacion",
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="historialodontograma",
            name="evolucion",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="historial_odontograma",
                to="fichas.evolucionclinica",
            ),
        ),
        migrations.AddField(
            model_name="historialodontograma",
            name="cita",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="historial_odontograma",
                to="agenda.cita",
            ),
        ),
        migrations.AddField(
            model_name="historialodontograma",
            name="estado_anterior",
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name="historialodontograma",
            name="estado_nuevo",
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddIndex(
            model_name="odontograma",
            index=models.Index(fields=["id_evolucion"], name="idx_odontogramas_evolucion"),
        ),
        migrations.AddIndex(
            model_name="odontograma",
            index=models.Index(fields=["id_odontologo"], name="idx_odontogramas_odonto"),
        ),
        migrations.RunPython(seed_catalogo_odontograma, noop_reverse),
    ]
