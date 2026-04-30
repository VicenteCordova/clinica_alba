"""
apps/antecedentes/models.py

Tablas: catalogo_antecedentes, registros_antecedentes_medicos, registro_antecedente_detalle
"""
from django.db import models
from django.utils import timezone


class CatalogoAntecedente(models.Model):
    """Tabla: catalogo_antecedentes"""

    TIPO_ALERGIA = "alergia"
    TIPO_ENFERMEDAD = "enfermedad_base"
    TIPO_MEDICAMENTO = "medicamento"
    TIPO_CONTRAINDICACION = "contraindicacion"
    TIPO_OTRO = "otro"
    TIPO_CHOICES = [
        (TIPO_ALERGIA, "Alergia"),
        (TIPO_ENFERMEDAD, "Enfermedad base"),
        (TIPO_MEDICAMENTO, "Medicamento"),
        (TIPO_CONTRAINDICACION, "Contraindicación"),
        (TIPO_OTRO, "Otro"),
    ]

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_CHOICES = [(ESTADO_ACTIVO, "Activo"), (ESTADO_INACTIVO, "Inactivo")]

    id_catalogo_antecedente = models.AutoField(primary_key=True)
    tipo_antecedente = models.CharField(max_length=30, choices=TIPO_CHOICES)
    nombre = models.CharField(max_length=120)
    descripcion = models.CharField(max_length=200, null=True, blank=True)
    estado_antecedente = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )

    class Meta:
        db_table = "catalogo_antecedentes"
        unique_together = [("tipo_antecedente", "nombre")]
        verbose_name = "Catálogo de Antecedente"
        verbose_name_plural = "Catálogo de Antecedentes"
        ordering = ["tipo_antecedente", "nombre"]

    def __str__(self):
        return f"[{self.get_tipo_antecedente_display()}] {self.nombre}"


class RegistroAntecedentesMedicos(models.Model):
    """Tabla: registros_antecedentes_medicos"""

    id_registro_antecedente = models.AutoField(primary_key=True)
    id_paciente = models.ForeignKey(
        "pacientes.Paciente",
        db_column="id_paciente",
        on_delete=models.RESTRICT,
        related_name="registros_antecedentes",
    )
    fecha_registro = models.DateTimeField(default=timezone.now)
    observaciones_generales = models.TextField(null=True, blank=True)
    id_usuario_registra = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_registra",
        on_delete=models.RESTRICT,
        related_name="antecedentes_registrados",
    )

    class Meta:
        db_table = "registros_antecedentes_medicos"
        verbose_name = "Registro de Antecedentes"
        verbose_name_plural = "Registros de Antecedentes"
        ordering = ["-fecha_registro"]
        indexes = [
            models.Index(fields=["id_paciente"], name="idx_reg_antecedentes_paciente"),
        ]

    def __str__(self):
        return f"Antecedentes de {self.id_paciente} — {self.fecha_registro:%d/%m/%Y}"


class RegistroAntecedenteDetalle(models.Model):
    """Tabla: registro_antecedente_detalle (PK compuesta)"""

    id_registro_antecedente = models.ForeignKey(
        RegistroAntecedentesMedicos,
        db_column="id_registro_antecedente",
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    id_catalogo_antecedente = models.ForeignKey(
        CatalogoAntecedente,
        db_column="id_catalogo_antecedente",
        on_delete=models.RESTRICT,
        related_name="registros_detalle",
    )
    detalle_adicional = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = "registro_antecedente_detalle"
        unique_together = [("id_registro_antecedente", "id_catalogo_antecedente")]
        verbose_name = "Detalle de Antecedente"
        verbose_name_plural = "Detalles de Antecedentes"

    def __str__(self):
        return str(self.id_catalogo_antecedente)
