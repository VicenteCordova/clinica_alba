"""
apps/fichas/models.py

Tablas: fichas_clinicas, evoluciones_clinicas, adjuntos_clinicos
"""
import os
from django.db import models
from django.utils import timezone
from apps.core.models import InhabilitableModel, AuditableModel
from django.core.exceptions import ValidationError
from django.conf import settings
from apps.core.enums import EstadoFichaEnum


def adjunto_upload_path(instance, filename):
    """Guarda adjuntos en media/adjuntos_clinicos/<id_evolucion>/<filename>"""
    return os.path.join(
        "adjuntos_clinicos",
        str(instance.id_evolucion_id),
        filename,
    )


class FichaClinica(InhabilitableModel, AuditableModel):
    """Tabla: fichas_clinicas"""

    id_ficha_clinica = models.AutoField(primary_key=True)
    id_paciente = models.OneToOneField(
        "pacientes.Paciente",
        db_column="id_paciente",
        on_delete=models.RESTRICT,
        related_name="ficha_clinica",
    )
    numero_ficha = models.CharField(max_length=30, unique=True)
    fecha_apertura = models.DateField()
    estado_ficha = models.CharField(
        max_length=20, choices=EstadoFichaEnum.choices, default=EstadoFichaEnum.ACTIVA
    )
    observaciones_clinicas_generales = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "fichas_clinicas"
        verbose_name = "Ficha Clínica"
        verbose_name_plural = "Fichas Clínicas"
        permissions = [
            ("disable_fichaclinica", "Puede inhabilitar ficha clinica"),
            ("reactivate_fichaclinica", "Puede reactivar ficha clinica"),
        ]
        indexes = [
            models.Index(fields=["id_paciente"], name="idx_fichas_paciente"),
        ]

    def __str__(self):
        return f"Ficha {self.numero_ficha} — {self.id_paciente.nombre_completo}"


class EvolucionClinica(InhabilitableModel, AuditableModel):
    """
    Tabla: evoluciones_clinicas

    Relación 1:1 con cita (unique key en id_cita).
    """

    id_evolucion = models.AutoField(primary_key=True)
    id_cita = models.OneToOneField(
        "agenda.Cita",
        db_column="id_cita",
        on_delete=models.RESTRICT,
        related_name="evolucion",
    )
    id_ficha_clinica = models.ForeignKey(
        "fichas.FichaClinica",
        db_column="id_ficha_clinica",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="evoluciones",
    )
    id_odontologo = models.ForeignKey(
        "odontologos.Odontologo",
        db_column="id_odontologo",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="evoluciones_clinicas",
    )
    fecha_evolucion = models.DateTimeField(default=timezone.now)
    motivo_consulta = models.TextField(null=True, blank=True)
    anamnesis = models.TextField(null=True, blank=True)
    diagnostico = models.TextField(null=True, blank=True)
    procedimiento_realizado = models.TextField(null=True, blank=True)
    indicaciones = models.TextField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    tratamiento_sugerido = models.TextField(null=True, blank=True)
    proxima_accion = models.TextField(null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evoluciones_clinicas"
        verbose_name = "Evolución Clínica"
        verbose_name_plural = "Evoluciones Clínicas"
        permissions = [
            ("disable_evolucionclinica", "Puede inhabilitar evolucion clinica"),
            ("reactivate_evolucionclinica", "Puede reactivar evolucion clinica"),
        ]
        ordering = ["-fecha_evolucion"]
        indexes = [
            models.Index(fields=["id_cita"], name="idx_evoluciones_cita"),
        ]

    def __str__(self):
        return f"Evolución #{self.id_evolucion} — Cita #{self.id_cita_id}"

    @property
    def tiene_registro_minimo(self):
        campos = [
            self.motivo_consulta,
            self.anamnesis,
            self.diagnostico,
            self.procedimiento_realizado,
            self.indicaciones,
            self.tratamiento_sugerido,
            self.proxima_accion,
            self.observaciones,
        ]
        return any((campo or "").strip() for campo in campos)


class AdjuntoClinico(InhabilitableModel):
    """Tabla: adjuntos_clinicos"""

    EXTENSIONES_PERMITIDAS = [
        "pdf", "png", "jpg", "jpeg", "gif", "bmp",
        "doc", "docx", "xls", "xlsx",
    ]

    id_adjunto = models.AutoField(primary_key=True)
    id_evolucion = models.ForeignKey(
        EvolucionClinica,
        db_column="id_evolucion",
        on_delete=models.CASCADE,
        related_name="adjuntos",
    )
    nombre_archivo = models.CharField(max_length=150)
    ruta_archivo = models.FileField(
        upload_to=adjunto_upload_path,
        max_length=255,
    )
    tipo_mime = models.CharField(max_length=80)
    tamano_kb = models.PositiveIntegerField(null=True, blank=True)
    fecha_subida = models.DateTimeField(default=timezone.now)
    id_usuario_sube = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_sube",
        on_delete=models.RESTRICT,
        related_name="adjuntos_subidos",
    )

    class Meta:
        db_table = "adjuntos_clinicos"
        verbose_name = "Adjunto Clínico"
        verbose_name_plural = "Adjuntos Clínicos"
        permissions = [
            ("disable_adjuntoclinico", "Puede inhabilitar adjunto clinico"),
            ("reactivate_adjuntoclinico", "Puede reactivar adjunto clinico"),
            ("download_adjuntoclinico", "Puede descargar adjunto clinico"),
        ]

    def __str__(self):
        return self.nombre_archivo

    def clean(self):
        if self.ruta_archivo:
            ext = self.nombre_archivo.rsplit(".", 1)[-1].lower()
            if ext not in self.EXTENSIONES_PERMITIDAS:
                raise ValidationError(
                    f"Extensión no permitida: .{ext}. "
                    f"Permitidas: {', '.join(self.EXTENSIONES_PERMITIDAS)}"
                )
            max_kb = getattr(settings, "MAX_UPLOAD_MB", 10) * 1024
            if self.tamano_kb and self.tamano_kb > max_kb:
                raise ValidationError(
                    f"El archivo supera el tamaño máximo de "
                    f"{settings.MAX_UPLOAD_MB} MB."
                )
