"""
config/settings/demo.py
Settings de demostración — usa SQLite, sin MariaDB.
Solo para visualizar la UI del proyecto.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = "demo-secret-key-clinica-alba-2024-no-usar-en-produccion"
DEBUG = True
ALLOWED_HOSTS = ["*"]

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

# SQLite para demo (sin necesidad de MariaDB)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_demo.sqlite3",
    }
}

# Auth custom
AUTH_USER_MODEL = "accounts.Usuario"
AUTHENTICATION_BACKENDS = ["apps.accounts.backends.CustomAuthBackend"]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:index"
LOGOUT_REDIRECT_URL = "accounts:login"

SESSION_COOKIE_AGE = 28800
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = True

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
MAX_UPLOAD_MB = 10

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

from django.contrib.messages import constants as messages_constants
MESSAGE_TAGS = {
    messages_constants.DEBUG: "secondary",
    messages_constants.INFO: "info",
    messages_constants.SUCCESS: "success",
    messages_constants.WARNING: "warning",
    messages_constants.ERROR: "danger",
}

CLINICA_NOMBRE = "Clínica Odontológica El Alba"
CLINICA_RUT = "76.000.000-0"
CLINICA_DIRECCION = "Av. El Alba 1234, Las Condes, Santiago"
CLINICA_TELEFONO = "+56 2 2345 6789"
CLINICA_EMAIL = "contacto@clinicaelalba.cl"
