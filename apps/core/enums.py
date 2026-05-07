from django.db import models

class EstadoBase(models.TextChoices):
    ACTIVO = "activo", "Activo"
    INACTIVO = "inactivo", "Inactivo"

class EstadoCitaEnum(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    CONFIRMADA = "confirmada", "Confirmada"
    EN_ESPERA = "en_espera", "En Espera"
    ATENDIDA = "atendida", "Atendida"
    CANCELADA = "cancelada", "Cancelada"
    REPROGRAMADA = "reprogramada", "Reprogramada"

class EstadoFichaEnum(models.TextChoices):
    ACTIVA = "activa", "Activa"
    CERRADA = "cerrada", "Cerrada"
    BLOQUEADA = "bloqueada", "Bloqueada"

class EstadoPlanEnum(models.TextChoices):
    ACTIVO = "activo", "Activo"
    CERRADO = "cerrado", "Cerrado"
    ANULADO = "anulado", "Anulado"
    BORRADOR = "borrador", "Borrador"
    PROPUESTO = "propuesto", "Propuesto"
    ACEPTADO_PARCIAL = "aceptado_parcial", "Aceptado parcialmente"
    ACEPTADO = "aceptado", "Aceptado"
    RECHAZADO = "rechazado", "Rechazado"
    EN_CURSO = "en_curso", "En curso"
    SUSPENDIDO = "suspendido", "Suspendido"
    FINALIZADO = "finalizado", "Finalizado"

class EstadoDetallePlanEnum(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    APROBADO = "aprobado", "Aprobado"
    EN_CURSO = "en_curso", "En curso"
    REALIZADO = "realizado", "Realizado"
    SUSPENDIDO = "suspendido", "Suspendido"
    RECHAZADO = "rechazado", "Rechazado"
    ANULADO = "anulado", "Anulado"

class EstadoPresupuestoEnum(models.TextChoices):
    VIGENTE = "vigente", "Vigente"
    VENCIDO = "vencido", "Vencido"
    ACEPTADO = "aceptado", "Aceptado"
    RECHAZADO = "rechazado", "Rechazado"
    ANULADO = "anulado", "Anulado"
    PAGADO_PARCIAL = "pagado_parcial", "Pagado parcial"
    PAGADO_TOTAL = "pagado_total", "Pagado total"

class EstadoPagoEnum(models.TextChoices):
    VIGENTE = "vigente", "Vigente"
    ANULADO = "anulado", "Anulado"

class EstadoProfesionalEnum(models.TextChoices):
    ACTIVO = "activo", "Activo"
    INACTIVO = "inactivo", "Inactivo"
    SUSPENDIDO = "suspendido", "Suspendido"

class AccionImagenologiaEnum(models.TextChoices):
    VISUALIZACION = "visualizacion", "Visualización"
    DESCARGA = "descarga", "Descarga"

class CategoriaCondicionEnum(models.TextChoices):
    DIAGNOSTICO = "diagnostico", "Diagnóstico"
    TRATAMIENTO = "tratamiento", "Tratamiento"
    ESTADO_PIEZA = "estado_pieza", "Estado de pieza"
    PERIODONCIA = "periodoncia", "Periodoncia"
    URGENCIA = "urgencia", "Urgencia"
    OTRO = "otro", "Otro"

class EstadoClinicoEnum(models.TextChoices):
    SANO = "sano", "Sano / Sin registro"
    EXISTENTE = "existente", "Existente"
    CONDICION = "condicion", "Condición detectada"
    PLANIFICADO = "planificado", "Planificado"
    EN_TRATAMIENTO = "en_tratamiento", "En tratamiento"
    COMPLETADO = "completado", "Completado"
    AUSENTE = "ausente", "Ausente / Extraído"
    EXTRACCION_INDICADA = "extraccion_indicada", "Extracción indicada"
    URGENCIA = "urgencia", "Urgencia"
    ANULADO = "anulado", "Anulado"

class EstadoGeneralPiezaEnum(models.TextChoices):
    PRESENTE = "presente", "Presente"
    AUSENTE = "ausente", "Ausente"
    EXTRACCION_INDICADA = "extraccion_indicada", "Extracción Indicada"
    EXTRAIDO = "extraido", "Extraído"
    IMPLANTE = "implante", "Implante"
    NO_ERUPCIONADO = "no_erupcionado", "No Erupcionado"
    REMANENTE = "remanente", "Remanente Radicular"
