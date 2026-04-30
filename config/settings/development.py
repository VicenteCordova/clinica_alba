"""
config/settings/development.py
Settings para entorno de desarrollo local.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# Barra de debug en consola
INTERNAL_IPS = ["127.0.0.1"]

# Email en consola durante desarrollo
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Queries más lentas en consola (útil para detectar N+1)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",  # Cambiar a DEBUG para ver todas las queries
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}
