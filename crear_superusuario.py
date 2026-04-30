"""
Script de creación de superusuario inicial.
Ejecutar con: python manage.py shell < crear_superusuario.py
O simplemente usar: python crear_superusuario.py (ajustar settings antes)
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.personas.models import Persona, Sexo
from apps.accounts.models import Usuario, Rol, UsuarioRol

print("Creando superusuario inicial...")

sexo, _ = Sexo.objects.get_or_create(nombre="masculino")

persona, created = Persona.objects.get_or_create(
    rut="11.111.111-1",
    defaults={
        "nombres": "Administrador",
        "apellido_paterno": "Sistema",
        "id_sexo": sexo,
    }
)

if not Usuario.objects.filter(username="admin").exists():
    usuario = Usuario.objects.create(
        id_persona=persona,
        username="admin",
        estado_acceso="activo",
        is_staff=True,
        is_superuser=True,
    )
    usuario.set_password("Admin1234!")
    usuario.save()

    rol, _ = Rol.objects.get_or_create(
        nombre="administrador",
        defaults={"descripcion": "Control total del sistema", "estado_rol": "activo"}
    )
    UsuarioRol.objects.get_or_create(id_usuario=usuario, rol=rol)
    print(f"✅ Superusuario creado: username=admin / password=Admin1234!")
    print("   ⚠️  Cambia la contraseña inmediatamente en producción.")
else:
    print("ℹ️  El usuario 'admin' ya existe.")
