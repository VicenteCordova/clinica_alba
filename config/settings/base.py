"""
config/settings/base.py
Settings base compartidos entre todos los entornos.
"""
import os
from pathlib import Path
from decouple import config, Csv

# ── Rutas base ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Seguridad ──────────────────────────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# ── Aplicaciones ───────────────────────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "widget_tweaks",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.personas",
    "apps.pacientes",
    "apps.odontologos",
    "apps.agenda",
    "apps.fichas",
    "apps.antecedentes",
    "apps.odontograma",
    "apps.tratamientos",
    "apps.presupuestos",
    "apps.pagos",
    "apps.caja",
    "apps.dashboard",
    "apps.auditoria",
    "apps.imagenologia",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── Middleware ─────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.AuditoriaMiddleware",
]

ROOT_URLCONF = "config.urls"

# ── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.clinica_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ── Base de datos MariaDB ──────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_demo.sqlite3",
    }
}

# ── Auth custom ────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.Usuario"
AUTHENTICATION_BACKENDS = ["apps.accounts.backends.CustomAuthBackend"]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:index"
LOGOUT_REDIRECT_URL = "accounts:login"

# ── Sesiones ───────────────────────────────────────────────────────────────────
SESSION_COOKIE_AGE = 28800          # 8 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False       # True en producción con HTTPS
CSRF_COOKIE_HTTPONLY = True

# ── Internacionalización ───────────────────────────────────────────────────────
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# ── Archivos estáticos ─────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ── Media (adjuntos clínicos) ──────────────────────────────────────────────────
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
MAX_UPLOAD_MB = config("MAX_UPLOAD_MB", default=10, cast=int)

# ── PK por defecto ─────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Mensajes ───────────────────────────────────────────────────────────────────
from django.contrib.messages import constants as messages_constants

MESSAGE_TAGS = {
    messages_constants.DEBUG: "secondary",
    messages_constants.INFO: "info",
    messages_constants.SUCCESS: "success",
    messages_constants.WARNING: "warning",
    messages_constants.ERROR: "danger",
}

# ── Nombre de la clínica (disponible en templates vía context processor) ───────
CLINICA_NOMBRE = "Clínica Odontológica El Alba"
CLINICA_RUT = "76.000.000-0"
CLINICA_DIRECCION = "Av. El Alba 1234, Las Condes, Santiago"
CLINICA_TELEFONO = "+56 2 2345 6789"
CLINICA_EMAIL = "contacto@clinicaelalba.cl"

# Django Widget Tweaks
WIDGET_ERROR_CLASS = 'is-invalid'
