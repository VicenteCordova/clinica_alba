"""
Helpers de permisos por rol para flujos clinicos y financieros.
"""

ROLES_SUPERVISION = ("administrador", "director", "director_clinico")
ROLES_CLINICOS = ("odontologo", "imagenologia", *ROLES_SUPERVISION)
ROLES_ATENCION = ("odontologo", *ROLES_SUPERVISION)
ROLES_RECEPCION = ("recepcionista", "recepcion", "administrativo", *ROLES_SUPERVISION)
ROLES_CAJA = ("cajero", "administrativo", "recepcionista", "administrador")
ROLES_AUDITORIA = ("administrador", "director", "director_clinico", "auditor")
ROLES_USUARIOS = ("administrador",)


def tiene_algun_rol(usuario, roles) -> bool:
    if not getattr(usuario, "is_authenticated", False):
        return False
    return usuario.tiene_rol(*roles)


def puede_atender_cita(usuario, cita) -> bool:
    if not tiene_algun_rol(usuario, ROLES_ATENCION):
        return False
    if usuario.tiene_rol(*ROLES_SUPERVISION):
        return True
    return cita.id_odontologo_id and cita.id_odontologo.id_usuario_id == usuario.id_usuario


def puede_ver_clinico(usuario) -> bool:
    return tiene_algun_rol(usuario, ROLES_CLINICOS + ROLES_RECEPCION)


def puede_editar_clinico(usuario) -> bool:
    return tiene_algun_rol(usuario, ROLES_ATENCION)


def puede_ver_imagenologia(usuario) -> bool:
    return tiene_algun_rol(usuario, ROLES_CLINICOS)


def puede_editar_imagenologia(usuario) -> bool:
    return tiene_algun_rol(usuario, ROLES_CLINICOS)


def puede_gestionar_usuarios(usuario) -> bool:
    return tiene_algun_rol(usuario, ROLES_USUARIOS)


def puede_gestionar_caja(usuario) -> bool:
    return tiene_algun_rol(usuario, ROLES_CAJA)


def puede_ver_auditoria(usuario) -> bool:
    return tiene_algun_rol(usuario, ROLES_AUDITORIA)
