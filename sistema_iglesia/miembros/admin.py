from django.contrib import admin

from .models import Familia, Miembro, MiembroMinisterio, Ministerio


@admin.register(Familia)
class FamiliaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre_familia", "telefono", "fecha_registro")
    search_fields = ("nombre_familia",)


@admin.register(Ministerio)
class MinisterioAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(Miembro)
class MiembroAdmin(admin.ModelAdmin):
    list_display = ("id", "nombres", "apellidos", "familia", "telefono", "estado")
    list_filter = ("estado", "familia")
    search_fields = ("nombres", "apellidos", "telefono", "email")


@admin.register(MiembroMinisterio)
class MiembroMinisterioAdmin(admin.ModelAdmin):
    list_display = ("id", "miembro", "ministerio", "fecha_asignacion", "rol")
