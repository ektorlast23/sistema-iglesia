"""
URL configuration for config project.

Rutas del sistema y del login. El acceso a `/admin/` usa las cuentas de Django;
las pantallas del sistema usan `/cuentas/login/`.
"""

from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("cuentas/", include("django.contrib.auth.urls")),
    path("salud/", views.salud, name="salud"),
    path("miembros/", include("miembros.urls")),
    path("inventario/", include("inventario.urls")),
    path("eventos/", include("eventos.urls")),
    path("reportes/", include("reportes.urls")),
    path("admin/", admin.site.urls),
]

# Página propia en lugar del HTML plano de Django.
handler403 = "config.views.error_403"
