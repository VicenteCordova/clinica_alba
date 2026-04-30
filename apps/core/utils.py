"""
apps/core/utils.py

Funciones utilitarias reutilizables.
"""
import re
from datetime import date
from typing import Optional


def formatear_rut(rut: str) -> str:
    """
    Formatea un RUT chileno al formato XX.XXX.XXX-X.
    Acepta entradas con o sin puntos/guion.
    """
    rut = rut.upper().replace(".", "").replace("-", "").strip()
    if len(rut) < 2:
        return rut
    cuerpo = rut[:-1]
    dv = rut[-1]
    # Formatear con puntos
    cuerpo_formateado = ""
    for i, c in enumerate(reversed(cuerpo)):
        if i > 0 and i % 3 == 0:
            cuerpo_formateado = "." + cuerpo_formateado
        cuerpo_formateado = c + cuerpo_formateado
    return f"{cuerpo_formateado}-{dv}"


def validar_rut(rut: str) -> bool:
    """
    Valida un RUT chileno usando el algoritmo del módulo 11.
    Acepta el formato XX.XXX.XXX-X o XXXXXXXX-X.
    """
    rut = rut.upper().replace(".", "").replace("-", "").strip()
    if not re.match(r"^\d{7,8}[0-9K]$", rut):
        return False
    cuerpo = rut[:-1]
    dv = rut[-1]
    suma = 0
    factor = 2
    for c in reversed(cuerpo):
        suma += int(c) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        dv_calculado = "0"
    elif resto == 10:
        dv_calculado = "K"
    else:
        dv_calculado = str(resto)
    return dv == dv_calculado


def calcular_edad(fecha_nacimiento: Optional[date]) -> Optional[int]:
    """Calcula la edad en años completos a partir de la fecha de nacimiento."""
    if not fecha_nacimiento:
        return None
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    return edad


def generar_numero_correlativo(modelo, campo: str, prefijo: str, longitud: int = 6) -> str:
    """
    Genera un número correlativo único con prefijo.
    Ejemplo: 'PRES-000001'
    """
    ultimo = modelo.objects.order_by(f"-{campo}").first()
    if ultimo:
        valor_actual = getattr(ultimo, campo)
        try:
            numero = int(valor_actual.replace(prefijo, "").replace("-", "")) + 1
        except (ValueError, AttributeError):
            numero = 1
    else:
        numero = 1
    return f"{prefijo}-{str(numero).zfill(longitud)}"
