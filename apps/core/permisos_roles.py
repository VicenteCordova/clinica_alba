"""
apps/core/permisos_roles.py

Mapeo de roles de la Clínica El Alba a permisos de Django.
Permite evaluar si un usuario tiene un permiso específico (ej. pacientes.can_view_paciente)
según sus roles en el sistema (ej. odontologo).
"""

# Lista de todos los modelos a los que les asignamos permisos
MODELOS = [
    ("pacientes", "paciente"),
    ("fichas", "fichaclinica"),
    ("fichas", "evolucionclinica"),
    ("fichas", "adjuntoclinico"),
    ("agenda", "cita"),
    ("odontograma", "odontograma"),
    ("tratamientos", "tratamiento"),
    ("tratamientos", "plantratamiento"),
    ("presupuestos", "presupuesto"),
    ("pagos", "pago"),
    ("imagenologia", "examenimagenologico"),
    ("imagenologia", "archivoexamenimagenologico"),
    ("antecedentes", "antecedente"),
    ("auditoria", "bitacora"),
    ("accounts", "usuario"),
    ("accounts", "rol"),
]

# Definición de las listas de acceso base por rol
MAPA_PERMISOS = {
    "administrador": set(), # El administrador tiene todo, se llenará dinámicamente o se maneja en has_perm
    "director_clinico": set(),
    "odontologo": set(),
    "asistente_dental": set(),
    "recepcionista": set(),
    "cajero": set(),
    "auditor": set(),
    "paciente": set(),
}

# Llenar dinámicamente todos los permisos para el administrador
for app_label, model_name in MODELOS:
    for accion in ["view", "add", "change", "disable", "reactivate", "download", "open_viewer"]:
        MAPA_PERMISOS["administrador"].add(f"{app_label}.{accion}_{model_name}")
        MAPA_PERMISOS["director_clinico"].add(f"{app_label}.{accion}_{model_name}")

# RECEPCION: Pacientes y Citas (solo administrativos)
for app_label, model_name in [("pacientes", "paciente"), ("agenda", "cita")]:
    for accion in ["view", "add", "change"]:
        MAPA_PERMISOS["recepcionista"].add(f"{app_label}.{accion}_{model_name}")
# Recepcion puede ver presupuestos y pagos
for app_label, model_name in [("presupuestos", "presupuesto"), ("pagos", "pago")]:
    MAPA_PERMISOS["recepcionista"].add(f"{app_label}.view_{model_name}")

# CAJA: Pagos, presupuestos, pacientes, citas
for app_label, model_name in [("pagos", "pago"), ("presupuestos", "presupuesto")]:
    for accion in ["view", "add", "change", "disable"]:
        MAPA_PERMISOS["cajero"].add(f"{app_label}.{accion}_{model_name}")
for app_label, model_name in [("pacientes", "paciente"), ("agenda", "cita")]:
    MAPA_PERMISOS["cajero"].add(f"{app_label}.view_{model_name}")

# ODONTOLOGO: Todo lo clínico
MODULOS_CLINICOS = [
    ("pacientes", "paciente"),
    ("fichas", "fichaclinica"),
    ("fichas", "evolucionclinica"),
    ("fichas", "adjuntoclinico"),
    ("agenda", "cita"),
    ("odontograma", "odontograma"),
    ("tratamientos", "plantratamiento"),
    ("presupuestos", "presupuesto"),
    ("imagenologia", "examenimagenologico"),
    ("imagenologia", "archivoexamenimagenologico"),
    ("antecedentes", "antecedente"),
]
for app_label, model_name in MODULOS_CLINICOS:
    for accion in ["view", "add", "change", "disable", "download"]:
        MAPA_PERMISOS["odontologo"].add(f"{app_label}.{accion}_{model_name}")
# Permiso específico para abrir visor CBCT
MAPA_PERMISOS["odontologo"].add("imagenologia.open_viewer_examenimagenologico")

# ASISTENTE DENTAL: Carga de archivos, apoyo, lectura clínica
for app_label, model_name in MODULOS_CLINICOS:
    MAPA_PERMISOS["asistente_dental"].add(f"{app_label}.view_{model_name}")
# Puede agregar/editar adjuntos
for accion in ["add", "change"]:
    MAPA_PERMISOS["asistente_dental"].add(f"fichas.{accion}_adjuntoclinico")
    MAPA_PERMISOS["asistente_dental"].add(f"imagenologia.{accion}_archivoexamenimagenologico")
    MAPA_PERMISOS["asistente_dental"].add(f"imagenologia.{accion}_examenimagenologico")

# AUDITOR: Solo vista y ver bitácora
for app_label, model_name in MODELOS:
    MAPA_PERMISOS["auditor"].add(f"{app_label}.view_{model_name}")

# PACIENTE: Solo vista de sus cosas autorizadas (la autorización a nivel de objeto se hace en vistas)
MAPA_PERMISOS["paciente"].add("pacientes.view_paciente")
MAPA_PERMISOS["paciente"].add("agenda.view_cita")
MAPA_PERMISOS["paciente"].add("presupuestos.view_presupuesto")
MAPA_PERMISOS["paciente"].add("pagos.view_pago")
MAPA_PERMISOS["paciente"].add("fichas.download_adjuntoclinico")

# Vista del catálogo de tratamientos para todo el personal
for rol in ["odontologo", "asistente_dental", "recepcionista", "cajero", "auditor"]:
    MAPA_PERMISOS[rol].add("tratamientos.view_tratamiento")

# Aliases a los roles de MAPA_PERMISOS
ALIASES_ROLES = {
    "admin": "administrador",
    "director": "director_clinico",
    "recepcion": "recepcionista",
    "administrativo": "recepcionista",
    "asistente": "asistente_dental",
    "caja": "cajero",
}
