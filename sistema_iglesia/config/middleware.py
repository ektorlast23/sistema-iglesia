"""Middlewares de acceso del sistema.

1. `LoginObligatorioMiddleware`: sin sesión iniciada no se ve ninguna pantalla
   (salvo login y el chequeo de salud, que Django marca como públicos).
2. `PermisosPorRolMiddleware`: aunque haya sesión, un rol de solo lectura no
   puede enviar formularios, y solo el Administrador puede eliminar.

Durante `manage.py test` la variable `REQUIERE_LOGIN` está apagada para no
romper las pruebas de las semanas anteriores, que no simulan sesión. Las pruebas
de permisos la encienden con `override_settings`.
"""

from django.conf import settings
from django.contrib.auth.middleware import LoginRequiredMiddleware
from django.shortcuts import render

from .permisos import MODULOS, puede_eliminar, puede_escribir

METODOS_ESCRITURA = {"POST", "PUT", "PATCH", "DELETE"}


class LoginObligatorioMiddleware(LoginRequiredMiddleware):
    """Variante que se puede desactivar por configuración (pruebas).

    Django ejecuta el control de acceso por `process_view`, no por `__call__`:
    anular solo `__call__` no alcanza. Hay que anular `process_view` para que
    `REQUIERE_LOGIN = False` realmente desactive el login obligatorio.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not getattr(settings, "REQUIERE_LOGIN", True):
            return None
        return super().process_view(request, view_func, view_args, view_kwargs)


class PermisosPorRolMiddleware:
    """Bloquea escrituras y eliminaciones según el rol del usuario."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not getattr(settings, "REQUIERE_LOGIN", True):
            return None
        if request.method not in METODOS_ESCRITURA:
            return None

        match = getattr(request, "resolver_match", None)
        app = getattr(match, "app_name", "") or ""
        if app not in MODULOS:
            return None

        nombre_vista = getattr(match, "url_name", "") or ""
        if "eliminar" in nombre_vista:
            permitido = puede_eliminar(request.user)
            motivo = (
                "Solo el rol Administrador puede eliminar o dar de baja registros."
            )
        else:
            permitido = puede_escribir(request.user, app)
            motivo = (
                "Tu rol es de solo lectura para este módulo. "
                "Pedí acceso a un administrador si necesitás cargar datos."
            )

        if permitido:
            return None
        return render(
            request,
            "403.html",
            {"motivo": motivo, "modulo": app},
            status=403,
        )
