"""Reglas de acceso por rol del Sistema de Gestión.

Los roles son grupos de Django. El middleware `PermisosPorRolMiddleware` decide
si un usuario puede escribir en cada módulo y el comando `crear_roles` deja los
grupos creados con sus permisos de modelo (para que el admin de Django muestre
lo mismo).

| Rol                     | Escribe en                          | Elimina |
|-------------------------|-------------------------------------|---------|
| Administrador           | todo                                | sí      |
| Secretaría              | miembros y eventos (asistencia)     | no      |
| Encargado de inventario | inventario (equipos y préstamos)    | no      |
| Consulta                | nada (solo lectura y reportes)      | no      |

Cualquier usuario autenticado puede consultar todos los módulos y descargar
reportes; lo que se restringe es la escritura.
"""

from django.conf import settings

GRUPO_ADMIN = "Administrador"
GRUPO_SECRETARIA = "Secretaría"
GRUPO_INVENTARIO = "Encargado de inventario"
GRUPO_CONSULTA = "Consulta"

GRUPOS = (GRUPO_ADMIN, GRUPO_SECRETARIA, GRUPO_INVENTARIO, GRUPO_CONSULTA)

# Módulos de la aplicación (coinciden con el app_name de cada urls.py).
MODULOS = ("miembros", "eventos", "inventario")

# Quién puede crear/editar en cada módulo.
EDITORES = {
    "miembros": {GRUPO_ADMIN, GRUPO_SECRETARIA},
    "eventos": {GRUPO_ADMIN, GRUPO_SECRETARIA},
    "inventario": {GRUPO_ADMIN, GRUPO_INVENTARIO},
}


def grupos_de(usuario):
    """Nombres de los grupos del usuario, o conjunto vacío si es anónimo."""
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return set()
    return set(usuario.groups.values_list("name", flat=True))


def es_admin(usuario):
    """El superusuario y el rol Administrador tienen control total."""
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return False
    return bool(usuario.is_superuser) or GRUPO_ADMIN in grupos_de(usuario)


def puede_escribir(usuario, modulo):
    """True si el usuario puede crear o editar registros del módulo."""
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return False
    if usuario.is_superuser:
        return True
    return bool(EDITORES.get(modulo, set()) & grupos_de(usuario))


def puede_eliminar(usuario):
    """Solo el Administrador puede borrar o dar de baja registros."""
    return es_admin(usuario)


def resumen_permisos(usuario):
    """Diccionario que consumen las plantillas para mostrar u ocultar botones."""
    # Con el login apagado (pruebas y desarrollo sin cuentas) tampoco se
    # restringe la escritura: las pruebas de las semanas 5-9 no inician sesión
    # y deben seguir viendo los formularios y sus errores.
    if not getattr(settings, "REQUIERE_LOGIN", True):
        return {
            "es_admin": True,
            "puede_eliminar": True,
            "puede_editar_miembros": True,
            "puede_editar_eventos": True,
            "puede_editar_inventario": True,
            "puede_escribir_algo": True,
            "roles": sorted(grupos_de(usuario)),
            "autenticado": bool(getattr(usuario, "is_authenticated", False)),
        }

    return {
        "es_admin": es_admin(usuario),
        "puede_eliminar": puede_eliminar(usuario),
        "puede_editar_miembros": puede_escribir(usuario, "miembros"),
        "puede_editar_eventos": puede_escribir(usuario, "eventos"),
        "puede_editar_inventario": puede_escribir(usuario, "inventario"),
        "puede_escribir_algo": any(
            puede_escribir(usuario, modulo) for modulo in MODULOS
        ),
        "roles": sorted(grupos_de(usuario)),
        "autenticado": bool(getattr(usuario, "is_authenticated", False)),
    }
