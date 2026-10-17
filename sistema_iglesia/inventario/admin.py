from django.contrib import admin

from .models import Equipo, Prestamo


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "cantidad", "estado", "ubicacion")
    list_filter = ("categoria", "estado")
    search_fields = ("nombre", "ubicacion")


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ("equipo", "miembro", "cantidad", "fecha_prestamo", "estado")
    list_filter = ("estado",)
    search_fields = ("equipo__nombre", "miembro__nombres", "miembro__apellidos")
