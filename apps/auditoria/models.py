"""
apps/auditoria/models.py

Tabla: bitacora
"""
from django.db import models
from django.utils import timezone


class Bitacora(models.Model):
    """
    Tabla: bitacora

    Registra acciones relevantes del sistema:
    login, creación, edición, eliminación, cambios de estado.
    """

    id_bitacora = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario",
        on_delete=models.RESTRICT,
        related_name="bitacora",
    )
    rol_usuario = models.CharField(max_length=120, null=True, blank=True)
    modulo = models.CharField(max_length=50)
    accion = models.CharField(max_length=50)
    tabla_afectada = models.CharField(max_length=50)
    id_registro_afectado = models.CharField(max_length=50)
    objeto_afectado = models.CharField(max_length=150, null=True, blank=True)
    paciente = models.ForeignKey(
        "pacientes.Paciente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_auditoria",
    )
    cita = models.ForeignKey(
        "agenda.Cita",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_auditoria",
    )
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    fecha_evento = models.DateTimeField(default=timezone.now)
    ip_origen = models.CharField(max_length=45, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    datos_anteriores = models.JSONField(null=True, blank=True)
    datos_nuevos = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "bitacora"
        verbose_name = "Registro de Bitácora"
        verbose_name_plural = "Bitácora"
        ordering = ["-fecha_evento"]
        indexes = [
            models.Index(fields=["id_usuario"], name="idx_bitacora_usuario"),
            models.Index(fields=["id_usuario", "fecha_evento"], name="idx_bitacora_usr_fecha"),
            models.Index(fields=["paciente", "fecha_evento"], name="idx_bitacora_paciente_fecha"),
            models.Index(fields=["cita", "fecha_evento"], name="idx_bitacora_cita_fecha"),
        ]

    def __str__(self):
        return (
            f"[{self.fecha_evento:%d/%m/%Y %H:%M}] "
            f"{self.id_usuario.username} — "
            f"{self.accion} en {self.tabla_afectada}"
        )

    @classmethod
    def registrar(
        cls,
        usuario,
        modulo: str,
        accion: str,
        tabla_afectada: str,
        id_registro_afectado,
        descripcion: str = None,
        ip_origen: str = None,
        request=None,
        paciente=None,
        cita=None,
        objeto_afectado: str = None,
        datos_anteriores=None,
        datos_nuevos=None,
        user_agent: str = None,
    ):
        """
        Método de clase para registrar una entrada de bitácora de forma conveniente.

        Uso:
            Bitacora.registrar(
                usuario=request.user,
                modulo='pacientes',
                accion='creacion',
                tabla_afectada='pacientes',
                id_registro_afectado=paciente.id_paciente,
                descripcion='Paciente Juan Pérez creado',
                ip_origen=request.ip_origen,
            )
        """
        if request is not None:
            ip_origen = ip_origen or getattr(request, "ip_origen", None)
            user_agent = user_agent or request.META.get("HTTP_USER_AGENT", "")[:255]

        roles = ""
        if usuario and getattr(usuario, "is_authenticated", False):
            try:
                roles = ", ".join(usuario.get_roles())
            except Exception:
                roles = ""

        cls.objects.create(
            id_usuario=usuario,
            rol_usuario=roles,
            modulo=modulo,
            accion=accion,
            tabla_afectada=tabla_afectada,
            id_registro_afectado=str(id_registro_afectado),
            objeto_afectado=objeto_afectado,
            paciente=paciente,
            cita=cita,
            descripcion=descripcion,
            fecha_evento=timezone.now(),
            ip_origen=ip_origen,
            user_agent=user_agent,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
        )
