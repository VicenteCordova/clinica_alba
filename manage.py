"""
manage.py — Clínica Odontológica El Alba
"""
import os
import sys

try:
    import pymysql
except ImportError:
    pymysql = None

if pymysql:
    pymysql.install_as_MySQLdb()


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Verifica que esté instalado y "
            "que el entorno virtual esté activo."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
