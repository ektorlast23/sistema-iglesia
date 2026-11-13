"""Context processor: permisos del usuario disponibles en todas las plantillas."""

from .permisos import resumen_permisos


def permisos(request):
    return {"permisos": resumen_permisos(getattr(request, "user", None))}
