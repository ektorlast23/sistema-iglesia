"""URLs del modulo de miembros (Semana 5)."""

from django.urls import path

from . import views

app_name = "miembros"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.registrar, name="registrar"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/eliminar/", views.eliminar, name="eliminar"),
]
