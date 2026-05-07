from django.db import models
from django.conf import settings

class InhabilitableModel(models.Model):
    """
    Modelo abstracto para habilitar el borrado lógico en lugar del borrado físico.
    """
    activo = models.BooleanField(default=True)
    fecha_inhabilitacion = models.DateTimeField(null=True, blank=True)
    motivo_inhabilitacion = models.TextField(null=True, blank=True)
    inhabilitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="%(class)s_inhabilitados",
        on_delete=models.SET_NULL,
    )

    class Meta:
        abstract = True

    def inhabilitar(self, usuario, motivo: str):
        from django.utils import timezone
        self.activo = False
        self.inhabilitado_por = usuario
        self.fecha_inhabilitacion = timezone.now()
        self.motivo_inhabilitacion = motivo
        self.save(update_fields=['activo', 'inhabilitado_por', 'fecha_inhabilitacion', 'motivo_inhabilitacion'])

    def reactivar(self):
        self.activo = True
        self.inhabilitado_por = None
        self.fecha_inhabilitacion = None
        self.motivo_inhabilitacion = None
        self.save(update_fields=['activo', 'inhabilitado_por', 'fecha_inhabilitacion', 'motivo_inhabilitacion'])


class AuditableModel(models.Model):
    """
    Modelo abstracto para registrar quién crea o actualiza un registro.
    """
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="%(class)s_creados",
        on_delete=models.SET_NULL,
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="%(class)s_actualizados",
        on_delete=models.SET_NULL,
    )

    class Meta:
        abstract = True
