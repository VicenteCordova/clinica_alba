# Generated manually for demo access bootstrap.

from django.contrib.auth.hashers import make_password
from django.db import migrations


ROLES = {
    "administrador": "Acceso maximo a configuracion, usuarios, caja, clinica y auditoria.",
    "administrativo": "Recepcion y gestion administrativa de pacientes, citas, pagos y saldos.",
    "recepcionista": "Recepcion, agenda, pacientes y apoyo administrativo.",
    "odontologo": "Atencion clinica, evoluciones, odontograma, imagenologia y planes.",
    "cajero": "Pagos, comprobantes, caja y movimientos financieros.",
    "director_clinico": "Supervision clinica, auditoria clinica y reportes.",
    "imagenologia": "Gestion de examenes y adjuntos clinicos.",
    "auditor": "Consulta de bitacora y trazabilidad.",
}


USUARIOS = [
    {
        "username": "admin",
        "password": "Admin123*",
        "rut": "11.111.111-1",
        "nombres": "Administrador",
        "apellido_paterno": "General",
        "apellido_materno": "Sistema",
        "correo": "admin@clinicaelalba.local",
        "roles": ["administrador"],
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "username": "recepcion",
        "password": "Recepcion123*",
        "rut": "22.222.222-2",
        "nombres": "Recepcion",
        "apellido_paterno": "Principal",
        "apellido_materno": "Clinica",
        "correo": "recepcion@clinicaelalba.local",
        "roles": ["administrativo", "recepcionista"],
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "username": "odontologo1",
        "password": "Odonto123*",
        "rut": "33.333.333-3",
        "nombres": "Juan",
        "apellido_paterno": "Perez",
        "apellido_materno": "Clinica",
        "correo": "odontologo1@clinicaelalba.local",
        "roles": ["odontologo"],
        "numero_registro": "OD-TEST-001",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "username": "odontologo2",
        "password": "Odonto123*",
        "rut": "44.444.444-4",
        "nombres": "Camila",
        "apellido_paterno": "Soto",
        "apellido_materno": "Clinica",
        "correo": "odontologo2@clinicaelalba.local",
        "roles": ["odontologo"],
        "numero_registro": "OD-TEST-002",
        "is_staff": False,
        "is_superuser": False,
    },
]


def seed_roles_usuarios(apps, schema_editor):
    Rol = apps.get_model("accounts", "Rol")
    Usuario = apps.get_model("accounts", "Usuario")
    UsuarioRol = apps.get_model("accounts", "UsuarioRol")
    Persona = apps.get_model("personas", "Persona")
    Odontologo = apps.get_model("odontologos", "Odontologo")

    roles = {}
    for nombre, descripcion in ROLES.items():
        rol, _ = Rol.objects.update_or_create(
            nombre=nombre,
            defaults={"descripcion": descripcion, "estado_rol": "activo"},
        )
        roles[nombre] = rol

    for data in USUARIOS:
        persona, _ = Persona.objects.update_or_create(
            rut=data["rut"],
            defaults={
                "nombres": data["nombres"],
                "apellido_paterno": data["apellido_paterno"],
                "apellido_materno": data["apellido_materno"],
                "correo": data["correo"],
                "estado_persona": "activo",
            },
        )
        usuario, _ = Usuario.objects.update_or_create(
            username=data["username"],
            defaults={
                "id_persona": persona,
                "password_hash": make_password(data["password"]),
                "estado_acceso": "activo",
                "is_staff": data["is_staff"],
                "is_superuser": data["is_superuser"],
            },
        )
        for rol_nombre in data["roles"]:
            UsuarioRol.objects.get_or_create(id_usuario=usuario, rol=roles[rol_nombre])

        if "odontologo" in data["roles"]:
            Odontologo.objects.update_or_create(
                id_usuario=usuario,
                defaults={
                    "numero_registro": data["numero_registro"],
                    "duracion_cita_base_min": 30,
                    "estado_profesional": "activo",
                },
            )


def noop_reverse(apps, schema_editor):
    # No se eliminan usuarios ni roles en reversa para respetar eliminacion logica.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("odontologos", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_roles_usuarios, noop_reverse),
    ]
