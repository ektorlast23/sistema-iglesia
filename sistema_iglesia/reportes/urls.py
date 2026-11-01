"""URLs del módulo de reportes (Semana 8)."""

from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("", views.indice, name="indice"),
    path("<slug:clave>/", views.detalle, name="detalle"),
    path("<slug:clave>/<str:formato>/", views.exportar, name="exportar"),
]
