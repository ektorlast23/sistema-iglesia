"""Crea (o actualiza) los cuatro roles del sistema con sus permisos de modelo.

Uso:
    python manage.py crear_roles

Es idempotente: se puede correr en cada despliegue. Los permisos que asigna son
los de Django (view/add/change/delete) para que el admin muestre lo mismo que
aplica el middleware de la aplicación.
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from config.permisos import (
    GRUPO_ADMIN,
    GRUPO_CONSULTA,
    GRUPO_INVENTARIO,
    GRUPO_SECRETARIA,
)

APPS = ("miembros", "eventos", "inventario")

VER = ("view",)
EDITAR = ("view", "add", "change")
TOTAL = ("view", "add", "change", "delete")

# accion -> módulos donde se aplica
PLAN = {
    GRUPO_ADMIN: {app: TOTAL for app in APPS},
    GRUPO_SECRETARIA: {
        "miembros": EDITAR,
        "eventos": EDITAR,
        "inventario": VER,
    },
    GRUPO_INVENTARIO: {
        "miembros": VER,
        "eventos": VER,
        "inventario": EDITAR,
    },
    GRUPO_CONSULTA: {app: VER for app in APPS},
}


class Command(BaseCommand):
    help = "Crea los grupos Administrador, Secretaría, Encargado de inventario y Consulta."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Quita permisos sobrantes de estos grupos antes de asignar.",
        )

    def handle(self, *args, **opciones):
        permisos = Permission.objects.filter(
            content_type__app_label__in=APPS
        ).select_related("content_type")

        for nombre_grupo, por_app in PLAN.items():
            grupo, creado = Group.objects.get_or_create(name=nombre_grupo)
            if opciones["limpiar"]:
                grupo.permissions.clear()

            asignar = []
            for permiso in permisos:
                acciones = por_app.get(permiso.content_type.app_label)
                if not acciones:
                    continue
                if permiso.codename.split("_", 1)[0] in acciones:
                    asignar.append(permiso)

            grupo.permissions.set(asignar)
            estado = "creado" if creado else "actualizado"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{nombre_grupo}: {estado} con {len(asignar)} permisos"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Roles listos. Asigná cada usuario a un grupo desde /admin/ "
                "o con: manage.py shell -c \"...\"."
            )
        )
