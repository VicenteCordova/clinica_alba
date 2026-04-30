# Generated manually for Fase 7 clinical-financial linkage.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agenda", "0002_cita_idx_citas_estado_cita_idx_citas_fecha"),
        ("fichas", "0003_evolucionclinica_campos_atencion"),
        ("odontograma", "0003_odontograma_idx_odontogramas_ficha"),
        ("tratamientos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="plantratamiento",
            name="id_cita",
            field=models.ForeignKey(
                blank=True,
                db_column="id_cita",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="planes_tratamiento",
                to="agenda.cita",
            ),
        ),
        migrations.AddField(
            model_name="plantratamiento",
            name="id_evolucion",
            field=models.ForeignKey(
                blank=True,
                db_column="id_evolucion",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="planes_tratamiento",
                to="fichas.evolucionclinica",
            ),
        ),
        migrations.AddField(
            model_name="plantratamiento",
            name="id_odontograma",
            field=models.ForeignKey(
                blank=True,
                db_column="id_odontograma",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="planes_tratamiento",
                to="odontograma.odontograma",
            ),
        ),
    ]
