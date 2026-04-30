"""
apps/core/middleware.py

Middleware de auditoría: adjunta la IP real del request al objeto request
para que los servicios puedan registrarla en la bitácora.
"""
from django.utils.deprecation import MiddlewareMixin


class AuditoriaMiddleware(MiddlewareMixin):
    """
    Extrae la IP de origen y la agrega a request.ip_origen.
    Compatible con proxies inversos que usan X-Forwarded-For.
    """

    def process_request(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "0.0.0.0")
        request.ip_origen = ip
