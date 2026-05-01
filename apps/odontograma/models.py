"""
apps/odontograma/models.py

Tablas: piezas_dentales, caras_dentales, condiciones_odontologicas,
        odontogramas, odontograma_detalle
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class PiezaDental(models.Model):
    """
    Tabla: piezas_dentales
    PK: codigo_pieza_dental (VARCHAR — no auto-increment)
    """

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_CHOICES = [(ESTADO_ACTIVO, "Activo"), (ESTADO_INACTIVO, "Inactivo")]

    codigo_pieza_dental = models.CharField(max_length=10, primary_key=True)
    descripcion = models.CharField(max_length=100)
    estado_pieza = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )

    class Meta:
        db_table = "piezas_dentales"
        verbose_name = "Pieza Dental"
        verbose_name_plural = "Piezas Dentales"

    def __str__(self):
        return f"{self.codigo_pieza_dental} — {self.descripcion}"


class CaraDental(models.Model):
    """Tabla: caras_dentales"""

    id_cara_dental = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)

    class Meta:
        db_table = "caras_dentales"
        verbose_name = "Cara Dental"
        verbose_name_plural = "Caras Dentales"

    def __str__(self):
        return self.nombre


class CondicionOdontologica(models.Model):
    """Tabla: condiciones_odontologicas"""

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_CHOICES = [(ESTADO_ACTIVO, "Activo"), (ESTADO_INACTIVO, "Inactivo")]

    CATEGORIA_CHOICES = [
        ("diagnostico", "Diagnóstico"),
        ("tratamiento", "Tratamiento"),
        ("estado_pieza", "Estado de pieza"),
        ("periodoncia", "Periodoncia"),
        ("urgencia", "Urgencia"),
        ("otro", "Otro"),
    ]

    id_condicion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=150, null=True, blank=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default="otro")
    estado_condicion = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )

    class Meta:
        db_table = "condiciones_odontologicas"
        verbose_name = "Condición Odontológica"
        verbose_name_plural = "Condiciones Odontológicas"

    def __str__(self):
        return self.nombre


class Odontograma(models.Model):
    """
    Tabla: odontogramas

    Versionado: unique(id_ficha_clinica, version), version > 0.
    La versión se auto-incrementa en OdontogramaService.
    """

    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_CHOICES = [(ESTADO_ACTIVO, "Activo"), (ESTADO_INACTIVO, "Inactivo")]

    id_odontograma = models.AutoField(primary_key=True)
    id_ficha_clinica = models.ForeignKey(
        "fichas.FichaClinica",
        db_column="id_ficha_clinica",
        on_delete=models.RESTRICT,
        related_name="odontogramas",
    )
    id_evolucion = models.ForeignKey(
        "fichas.EvolucionClinica",
        db_column="id_evolucion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="odontogramas",
    )
    id_odontologo = models.ForeignKey(
        "odontologos.Odontologo",
        db_column="id_odontologo",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="odontogramas",
    )
    id_usuario_crea = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_crea",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="odontogramas_creados",
    )
    id_usuario_actualiza = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_actualiza",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="odontogramas_actualizados",
    )
    version = models.PositiveSmallIntegerField(default=1)
    fecha_registro = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    descripcion_general = models.TextField(null=True, blank=True)
    estado_odontograma = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )

    class Meta:
        db_table = "odontogramas"
        unique_together = [("id_ficha_clinica", "version")]
        verbose_name = "Odontograma"
        verbose_name_plural = "Odontogramas"
        ordering = ["-version"]
        indexes = [
            models.Index(fields=["id_ficha_clinica"], name="idx_odontogramas_ficha"),
            models.Index(fields=["id_evolucion"], name="idx_odontogramas_evolucion"),
            models.Index(fields=["id_odontologo"], name="idx_odontogramas_odonto"),
        ]

    def __str__(self):
        return f"Odontograma v{self.version} — Ficha {self.id_ficha_clinica_id}"

    def clean(self):
        if self.version is not None and self.version <= 0:
            raise ValidationError({"version": "La versión debe ser mayor que 0."})
        if self.id_evolucion_id:
            evolucion_ficha_id = self.id_evolucion.id_ficha_clinica_id
            if evolucion_ficha_id and evolucion_ficha_id != self.id_ficha_clinica_id:
                raise ValidationError(
                    {"id_evolucion": "La evolucion no pertenece a la ficha clinica del odontograma."}
                )
            if (
                self.id_odontologo_id
                and self.id_evolucion.id_odontologo_id
                and self.id_odontologo_id != self.id_evolucion.id_odontologo_id
            ):
                raise ValidationError(
                    {"id_odontologo": "El odontologo no coincide con la evolucion asociada."}
                )

    @property
    def paciente(self):
        return self.id_ficha_clinica.id_paciente


class OdontogramaDetalle(models.Model):
    """
    Tabla: odontograma_detalle

    Restricción única: (id_odontograma, codigo_pieza_dental, id_cara_dental)
    No puede haber dos condiciones para la misma cara de la misma pieza.
    """

    ESTADO_CLINICO_CHOICES = [
        ("sano", "Sano / Sin registro"),
        ("existente", "Existente"),
        ("condicion", "Condición detectada"),
        ("planificado", "Planificado"),
        ("en_tratamiento", "En tratamiento"),
        ("completado", "Completado"),
        ("ausente", "Ausente / Extraído"),
        ("extraccion_indicada", "Extracción indicada"),
        ("urgencia", "Urgencia"),
        ("anulado", "Anulado"),
    ]

    id_odontograma_detalle = models.AutoField(primary_key=True)
    id_odontograma = models.ForeignKey(
        Odontograma,
        db_column="id_odontograma",
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    codigo_pieza_dental = models.ForeignKey(
        PiezaDental,
        db_column="codigo_pieza_dental",
        to_field="codigo_pieza_dental",
        on_delete=models.RESTRICT,
        related_name="odontograma_detalles",
    )
    id_cara_dental = models.ForeignKey(
        CaraDental,
        db_column="id_cara_dental",
        on_delete=models.RESTRICT,
        related_name="odontograma_detalles",
    )
    id_condicion = models.ForeignKey(
        CondicionOdontologica,
        db_column="id_condicion",
        on_delete=models.RESTRICT,
        related_name="odontograma_detalles",
    )
    estado_clinico = models.CharField(
        max_length=30,
        choices=ESTADO_CLINICO_CHOICES,
        default="condicion",
    )
    observacion = models.CharField(max_length=150, null=True, blank=True)
    fecha_anulacion = models.DateTimeField(null=True, blank=True)
    motivo_anulacion = models.CharField(max_length=200, null=True, blank=True)
    id_usuario_anula = models.ForeignKey(
        "accounts.Usuario",
        db_column="id_usuario_anula",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="odontograma_detalles_anulados",
    )

    class Meta:
        db_table = "odontograma_detalle"
        unique_together = [("id_odontograma", "codigo_pieza_dental", "id_cara_dental")]
        verbose_name = "Detalle de Odontograma"
        verbose_name_plural = "Detalles de Odontograma"
        indexes = [
            models.Index(fields=["codigo_pieza_dental"], name="idx_odontograma_detalle_pieza"),
            models.Index(fields=["id_cara_dental"], name="idx_odontograma_detalle_cara"),
        ]

    def __str__(self):
        return (
            f"Pieza {self.codigo_pieza_dental_id} / "
            f"{self.id_cara_dental} → {self.id_condicion}"
        )

    def clean(self):
        from apps.odontograma.services import obtener_info_pieza

        if not self.codigo_pieza_dental_id or not self.id_cara_dental_id:
            return
        info = obtener_info_pieza(self.codigo_pieza_dental_id)
        caras_validas = set(info.get("caras_coronarias", []))
        cara = self.id_cara_dental.nombre
        if cara not in caras_validas:
            raise ValidationError(
                {"id_cara_dental": f"La cara {cara} no corresponde a la pieza {self.codigo_pieza_dental_id}."}
            )


class OdontogramaPieza(models.Model):
    """Estado general y observaciones a nivel de pieza completa."""
    id = models.AutoField(primary_key=True)
    odontograma = models.ForeignKey(Odontograma, on_delete=models.CASCADE, related_name="piezas")
    codigo_pieza_dental = models.ForeignKey(PiezaDental, on_delete=models.RESTRICT)
    
    ESTADO_GENERAL_CHOICES = [
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('extraccion_indicada', 'Extracción Indicada'),
        ('extraido', 'Extraído'),
        ('implante', 'Implante'),
        ('no_erupcionado', 'No Erupcionado'),
        ('remanente', 'Remanente Radicular'),
    ]
    estado_general = models.CharField(max_length=30, choices=ESTADO_GENERAL_CHOICES, default='presente')
    observacion = models.TextField(blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "odontograma_pieza"
        unique_together = [("odontograma", "codigo_pieza_dental")]
        verbose_name = "Estado de Pieza"
        verbose_name_plural = "Estados de Piezas"


class OdontogramaRaiz(models.Model):
    """Representa el estado de una raíz específica de una pieza."""
    id = models.AutoField(primary_key=True)
    pieza = models.ForeignKey(OdontogramaPieza, on_delete=models.CASCADE, related_name="raices")
    
    RAIZ_CHOICES = [
        ('unica', 'Única'),
        ('mesial', 'Mesial'),
        ('distal', 'Distal'),
        ('palatina', 'Palatina'),
        ('mesiovestibular', 'Mesiovestibular'),
        ('distovestibular', 'Distovestibular'),
        ('vestibular', 'Vestibular'),
    ]
    raiz = models.CharField(max_length=20, choices=RAIZ_CHOICES)
    
    TERCIO_CHOICES = [
        ('cervical', 'Cervical'),
        ('medio', 'Medio'),
        ('apical', 'Apical'),
        ('completo', 'Completo'),
    ]
    tercio = models.CharField(max_length=20, choices=TERCIO_CHOICES, default='completo')
    
    id_condicion = models.ForeignKey(CondicionOdontologica, on_delete=models.RESTRICT, null=True, blank=True)
    observacion = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = "odontograma_raiz"
        unique_together = [("pieza", "raiz", "tercio")]


class OdontogramaPeriodontal(models.Model):
    """Información periodontal por pieza."""
    id = models.AutoField(primary_key=True)
    pieza = models.OneToOneField(OdontogramaPieza, on_delete=models.CASCADE, related_name="periodonto")
    
    movilidad = models.CharField(max_length=20, blank=True, null=True)  # Ej: Grado I, II, III
    profundidad_sondaje = models.CharField(max_length=50, blank=True, null=True) # Json o texto con profundidades M,V,D,P/L
    recesion = models.CharField(max_length=50, blank=True, null=True)
    sangrado = models.BooleanField(default=False)
    placa = models.BooleanField(default=False)
    supuracion = models.BooleanField(default=False)
    furca = models.CharField(max_length=20, blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "odontograma_periodontal"


class HistorialOdontograma(models.Model):
    """Bitácora clínica granular a nivel de pieza."""
    id = models.AutoField(primary_key=True)
    odontograma = models.ForeignKey(Odontograma, on_delete=models.CASCADE, related_name="historial")
    pieza_dental = models.ForeignKey(PiezaDental, on_delete=models.RESTRICT)
    evolucion = models.ForeignKey(
        "fichas.EvolucionClinica",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historial_odontograma",
    )
    cita = models.ForeignKey(
        "agenda.Cita",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historial_odontograma",
    )
    usuario = models.ForeignKey("accounts.Usuario", on_delete=models.SET_NULL, null=True)
    
    tipo_cambio = models.CharField(max_length=50) # 'estado_general', 'superficie', 'raiz', 'periodonto'
    detalle_cambio = models.TextField() # "Se cambió cara Oclusal de Sano a Caries"
    estado_anterior = models.CharField(max_length=150, null=True, blank=True)
    estado_nuevo = models.CharField(max_length=150, null=True, blank=True)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "odontograma_historial"
        ordering = ["-fecha"]
