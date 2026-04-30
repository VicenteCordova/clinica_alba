"""
apps/core/templatetags/core_tags.py

Custom template tags y filtros para el sistema.
"""
from django import template
from django.utils import timezone
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def rut_format(rut: str) -> str:
    """Formatea un RUT chileno: 12345678K → 12.345.678-K"""
    if not rut:
        return "—"
    rut = rut.replace(".", "").replace("-", "").upper()
    if len(rut) < 2:
        return rut
    cuerpo = rut[:-1]
    dv = rut[-1]
    cuerpo_formateado = ""
    for i, c in enumerate(reversed(cuerpo)):
        if i > 0 and i % 3 == 0:
            cuerpo_formateado = "." + cuerpo_formateado
        cuerpo_formateado = c + cuerpo_formateado
    return f"{cuerpo_formateado}-{dv}"


@register.filter
def edad(fecha) -> int:
    """Calcula la edad en años a partir de una fecha de nacimiento."""
    if not fecha:
        return None
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    hoy = date.today()
    return hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))


@register.filter
def pesos_cl(valor) -> str:
    """Formatea un valor como pesos chilenos: $1.234.567"""
    if valor is None:
        return "—"
    try:
        n = int(Decimal(str(valor)))
        return f"${n:,}".replace(",", ".")
    except (InvalidOperation, ValueError, TypeError):
        return str(valor)


@register.filter
def split(value, sep=","):
    """Divide una cadena por el separador dado y retorna una lista."""
    return [s.strip() for s in value.split(sep)]


@register.filter
def primera_mayuscula(value: str) -> str:
    """Capitaliza solo la primera letra."""
    return value[:1].upper() + value[1:] if value else value


@register.simple_tag(takes_context=True)
def url_activa(context, url_name: str) -> str:
    """Retorna 'active' si la URL actual corresponde al nombre dado."""
    try:
        from django.urls import reverse, NoReverseMatch
        request = context.get("request")
        if request and request.path.startswith(reverse(url_name)):
            return "active"
    except Exception:
        pass
    return ""


@register.inclusion_tag("partials/_messages.html", takes_context=True)
def mostrar_mensajes(context):
    return {"messages": context.get("messages", [])}

@register.filter
def filter_estado(citas, estado_nombre):
    """Filtra una lista de citas por el nombre de su estado."""
    if not citas:
        return []
    return [c for c in citas if c.id_estado_cita.nombre == estado_nombre]


@register.simple_tag(takes_context=True)
def tiene_rol(context, *roles):
    """Tag: {% tiene_rol 'admin' 'recepcionista' %} -> True/False
    Uso en if: {% if request.user|user_tiene_rol:'admin,recepcionista' %}
    """
    request = context.get('request')
    if not request or not hasattr(request, 'user'):
        return False
    user = request.user
    if not user.is_authenticated:
        return False
    if hasattr(user, 'tiene_rol'):
        return user.tiene_rol(*roles)
    return False


@register.filter(name='user_tiene_rol')
def user_tiene_rol(user, roles_str):
    """Filtro: {{ request.user|user_tiene_rol:'admin,recepcionista' }}"""
    if not user or not user.is_authenticated:
        return False
    roles = [r.strip() for r in roles_str.split(',')]
    if hasattr(user, 'tiene_rol'):
        return user.tiene_rol(*roles)
    return False


@register.filter(name='filter_estado')
def filter_estado(citas, estado):
    """Filtro: {{ citas|filter_estado:'en_espera' }} -> lista filtrada"""
    return [c for c in citas if hasattr(c, 'id_estado_cita') and c.id_estado_cita.nombre == estado]
