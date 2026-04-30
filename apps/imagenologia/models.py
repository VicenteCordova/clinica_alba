"""
apps/imagenologia/models.py

Modelos para el Módulo de Imagenología Odontológica y Exámenes CBCT/DICOM.
"""
import os
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings

def path_archivo_examen(instance, filename):
    """Genera la ruta de almacenamiento segura: media/imagenologia/paciente_id/uuid_filename"""
    ext = filename.split('.')[-1]
    nombre_seguro = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('imagenologia', str(instance.examen.paciente.id_paciente), nombre_seguro)


class TipoExamenImagenologico(models.Model):
    """Catálogo maestro de tipos de estudio"""
    ESTADO_ACTIVO = 'activo'
    ESTADO_INACTIVO = 'inactivo'
    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, 'Activo'),
        (ESTADO_INACTIVO, 'Inactivo'),
    ]

    id_tipo_examen = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "imagenologia_tipos_examen"
        verbose_name = "Tipo de Examen Imagenológico"
        verbose_name_plural = "Tipos de Examen Imagenológico"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class ExamenImagenologico(models.Model):
    """Contenedor principal del estudio clínico"""
    ESTADO_BORRADOR = 'borrador'
    ESTADO_FINALIZADO = 'finalizado'
    ESTADO_ANULADO = 'anulado'
    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_FINALIZADO, 'Finalizado'),
        (ESTADO_ANULADO, 'Anulado'),
    ]

    id_examen = models.AutoField(primary_key=True)
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.RESTRICT, related_name='examenes_imagenologicos')
    ficha_clinica = models.ForeignKey('fichas.FichaClinica', on_delete=models.SET_NULL, null=True, blank=True, related_name='examenes_imagenologicos')
    cita = models.ForeignKey('agenda.Cita', on_delete=models.SET_NULL, null=True, blank=True, related_name='examenes_imagenologicos')
    evolucion = models.ForeignKey('fichas.EvolucionClinica', on_delete=models.SET_NULL, null=True, blank=True, related_name='examenes_imagenologicos')
    tipo_examen = models.ForeignKey(TipoExamenImagenologico, on_delete=models.RESTRICT, related_name='examenes')
    
    fecha_examen = models.DateField(default=timezone.now)
    centro_radiologico = models.CharField(max_length=150, blank=True, null=True)
    titulo = models.CharField(max_length=200, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    observacion_clinica = models.TextField(blank=True, null=True)
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_FINALIZADO)
    
    solicitado_por = models.ForeignKey('odontologos.Odontologo', on_delete=models.SET_NULL, null=True, blank=True, related_name='examenes_solicitados')
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name='examenes_creados')
    
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    # Preparación futura para integración DICOM/CBCT
    study_instance_uid = models.CharField(max_length=255, blank=True, null=True, help_text="DICOM StudyInstanceUID")
    orthanc_study_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID en el servidor Orthanc PACS")

    class Meta:
        db_table = "imagenologia_examenes"
        verbose_name = "Examen Imagenológico"
        verbose_name_plural = "Exámenes Imagenológicos"
        ordering = ["-fecha_examen", "-id_examen"]
        indexes = [
            models.Index(fields=["paciente"]),
            models.Index(fields=["fecha_examen"]),
        ]

    def __str__(self):
        return f"Examen {self.tipo_examen.nombre} - {self.paciente.nombre_completo} ({self.fecha_examen})"


class ArchivoExamenImagenologico(models.Model):
    """Manejo físico de los archivos subidos al examen"""
    ESTADO_ACTIVO = 'activo'
    ESTADO_ANULADO = 'anulado'
    ESTADO_REEMPLAZADO = 'reemplazado'
    ESTADO_INACTIVO = ESTADO_ANULADO
    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, 'Activo'),
        (ESTADO_ANULADO, 'Anulado'),
        (ESTADO_REEMPLAZADO, 'Reemplazado'),
    ]

    id_archivo = models.AutoField(primary_key=True)
    examen = models.ForeignKey(ExamenImagenologico, on_delete=models.CASCADE, related_name='archivos')
    
    archivo = models.FileField(upload_to=path_archivo_examen, max_length=500)
    nombre_original = models.CharField(max_length=255)
    extension = models.CharField(max_length=20)
    tipo_mime = models.CharField(max_length=100)
    peso_bytes = models.BigIntegerField()
    
    es_principal = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO)
    
    subido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name='archivos_imagenologia_subidos')
    motivo_anulacion = models.TextField(null=True, blank=True)
    fecha_anulacion = models.DateTimeField(null=True, blank=True)
    usuario_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name='archivos_imagenologia_gestionados',
    )
    adjunto_reemplazo = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adjuntos_reemplazados',
    )
    fecha_subida = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "imagenologia_archivos"
        verbose_name = "Archivo de Examen"
        verbose_name_plural = "Archivos de Examen"

    def __str__(self):
        return f"Archivo {self.nombre_original} (Examen {self.examen_id})"


class ObservacionImagenologica(models.Model):
    """Anotaciones clínicas sobre el examen hechas por profesionales"""
    id_observacion = models.AutoField(primary_key=True)
    examen = models.ForeignKey(ExamenImagenologico, on_delete=models.CASCADE, related_name='observaciones')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name='observaciones_imagenologia')
    observacion = models.TextField()
    fecha_observacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "imagenologia_observaciones"
        verbose_name = "Observación Imagenológica"
        verbose_name_plural = "Observaciones Imagenológicas"
        ordering = ["-fecha_observacion"]

    def __str__(self):
        return f"Obs de {self.usuario} en Examen {self.examen_id}"


class AccesoExamenImagenologico(models.Model):
    """Auditoría de visualización o descarga de archivos clínicos sensibles"""
    ACCION_VISUALIZACION = 'visualizacion'
    ACCION_DESCARGA = 'descarga'
    ACCION_CHOICES = [
        (ACCION_VISUALIZACION, 'Visualización'),
        (ACCION_DESCARGA, 'Descarga'),
    ]

    id_acceso = models.AutoField(primary_key=True)
    archivo = models.ForeignKey(ArchivoExamenImagenologico, on_delete=models.CASCADE, related_name='accesos')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name='accesos_imagenologia')
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES)
    fecha_acceso = models.DateTimeField(default=timezone.now)
    ip_usuario = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "imagenologia_accesos_auditoria"
        verbose_name = "Auditoría de Acceso Imagenológico"
        verbose_name_plural = "Auditorías de Acceso Imagenológico"
        ordering = ["-fecha_acceso"]

    def __str__(self):
        return f"{self.usuario} - {self.accion} - Archivo {self.archivo_id}"
