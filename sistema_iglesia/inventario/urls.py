"""URLs del modulo de inventario (Semana 6)."""

from django.urls import path

from . import views

app_name = "inventario"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.registrar, name="registrar"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("prestamos/", views.prestamos, name="prestamos"),
    path("devoluciones/", views.devoluciones, name="devoluciones"),
]
