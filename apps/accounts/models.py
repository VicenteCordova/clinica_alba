"""
apps/accounts/models.py

Modelos de autenticación custom alineados con las tablas:
  - roles
  - usuarios
  - usuario_rol
"""
import unicodedata

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone


class Rol(models.Model):
    """Tabla: roles"""

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_INACTIVO, "Inactivo"),
    ]

    id_rol = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=150, null=True, blank=True)
    estado_rol = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )

    class Meta:
        db_table = "roles"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    """Manager custom para el modelo Usuario."""

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("El username es obligatorio.")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        """
        Crea un superusuario de Django admin.
        Requiere que exista una Persona previamente o la crea inline.
        """
        extra_fields.setdefault("estado_acceso", "activo")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra_fields)


class Usuario(AbstractBaseUser):
    """
    Tabla: usuarios

    Extiende AbstractBaseUser para mapear exactamente la tabla existente.
    No usa la tabla auth_user de Django.
    """

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_BLOQUEADO = "bloqueado"
    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_INACTIVO, "Inactivo"),
        (ESTADO_BLOQUEADO, "Bloqueado"),
    ]

    id_usuario = models.AutoField(primary_key=True)
    # FK a personas — importación diferida para evitar importación circular
    id_persona = models.OneToOneField(
        "personas.Persona",
        db_column="id_persona",
        on_delete=models.RESTRICT,
        related_name="usuario",
    )
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    estado_acceso = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    # Campos requeridos por Django admin (no en BD original, manejados en memoria)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # AbstractBaseUser usa 'password' internamente; mapeamos al campo real
    PASSWORD_FIELD = "password_hash"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    class Meta:
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.username

    # ── Propiedades requeridas por Django ──────────────────────────────────────
    @property
    def is_active(self):
        return self.estado_acceso == self.ESTADO_ACTIVO

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    # ── Helpers de rol ─────────────────────────────────────────────────────────
    @staticmethod
    def normalizar_nombre_rol(nombre: str) -> str:
        """Normaliza nombres de rol para tolerar mayusculas, espacios y acentos."""
        if not nombre:
            return ""
        texto = unicodedata.normalize("NFKD", str(nombre))
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        return texto.strip().lower().replace(" ", "_").replace("/", "_")

    @classmethod
    def expandir_alias_roles(cls, roles: tuple[str, ...]) -> set[str]:
        aliases = {
            "admin": {"administrador"},
            "administrador": {"administrador"},
            "administrativo": {"administrativo", "recepcionista", "recepcion"},
            "recepcion": {"recepcionista", "recepcion", "administrativo"},
            "recepcionista": {"recepcionista", "recepcion", "administrativo"},
            "administrativo_recepcion": {"administrativo", "recepcionista", "recepcion"},
            "odontologo": {"odontologo"},
            "odontologa": {"odontologo"},
            "cajero": {"cajero"},
            "caja": {"cajero"},
            "director": {"director", "director_clinico"},
            "director_clinico": {"director", "director_clinico"},
            "imagenologia": {"imagenologia"},
            "auditor": {"auditor"},
        }
        normalizados = {cls.normalizar_nombre_rol(rol) for rol in roles if rol}
        expandidos = set(normalizados)
        for rol in normalizados:
            expandidos.update(aliases.get(rol, set()))
        return expandidos

    def tiene_rol(self, *roles: str) -> bool:
        """Devuelve True si el usuario tiene al menos uno de los roles indicados."""
        if self.is_superuser:
            return True
        roles_requeridos = self.expandir_alias_roles(roles)
        if not roles_requeridos:
            return False
        roles_usuario = {
            self.normalizar_nombre_rol(nombre)
            for nombre in self.usuario_roles.filter(
                rol__estado_rol=Rol.ESTADO_ACTIVO
            ).values_list("rol__nombre", flat=True)
        }
        return bool(roles_usuario & roles_requeridos)

    def get_roles(self) -> list[str]:
        """Lista de nombres de roles del usuario."""
        return list(
            self.usuario_roles.filter(rol__estado_rol=Rol.ESTADO_ACTIVO)
            .values_list("rol__nombre", flat=True)
        )

    # ── Compatibilidad con AbstractBaseUser ────────────────────────────────────
    def get_password(self):
        return self.password_hash

    def set_password(self, raw_password):
        from django.contrib.auth.hashers import make_password
        self.password_hash = make_password(raw_password)
        self._password = raw_password

    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password as _check

        def setter(raw):
            self.set_password(raw)
            self.save(update_fields=["password_hash"])

        return _check(raw_password, self.password_hash, setter)

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, value):
        self.password_hash = value

    # ── Nombre legible ─────────────────────────────────────────────────────────
    @property
    def nombre_completo(self):
        try:
            return self.id_persona.nombre_completo
        except Exception:
            return self.username


class UsuarioRol(models.Model):
    """Tabla: usuario_rol (M2M con PK compuesta)"""

    id_usuario = models.ForeignKey(
        Usuario,
        db_column="id_usuario",
        on_delete=models.CASCADE,
        related_name="usuario_roles",
    )
    rol = models.ForeignKey(
        Rol,
        db_column="id_rol",
        on_delete=models.RESTRICT,
        related_name="usuario_roles",
    )

    class Meta:
        db_table = "usuario_rol"
        unique_together = [("id_usuario", "rol")]
        verbose_name = "Usuario-Rol"
        verbose_name_plural = "Usuarios-Roles"

    def __str__(self):
        return f"{self.id_usuario.username} → {self.rol.nombre}"
