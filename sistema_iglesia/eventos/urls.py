"""URLs del modulo de eventos (Semana 7)."""

from django.urls import path

from . import views

app_name = "eventos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.registrar, name="registrar"),
    path(
        "asistencias/miembro/",
        views.asistencia_consulta_miembro,
        name="asistencia_consulta_miembro",
    ),
    path(
        "asistencia/<int:pk>/editar/",
        views.asistencia_editar,
        name="asistencia_editar",
    ),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/eliminar/", views.eliminar, name="eliminar"),
    path(
        "<int:evento_id>/asistencia/nuevo/",
        views.asistencia_registrar,
        name="asistencia_registrar",
    ),
    path(
        "<int:evento_id>/asistencias/",
        views.lista_asistencias,
        name="lista_asistencias",
    ),
]
