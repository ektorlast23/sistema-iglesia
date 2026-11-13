"""Pruebas del control de acceso: login obligatorio y permisos por rol.

Las pruebas de las semanas 5-9 corren con `REQUIERE_LOGIN = False` (ver
`config/settings.py`) porque no simulan sesión. Estas pruebas lo encienden con
`override_settings` para verificar el comportamiento real de producción.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse

from config.permisos import (
    GRUPO_ADMIN,
    GRUPO_CONSULTA,
    GRUPO_INVENTARIO,
    GRUPO_SECRETARIA,
)

Usuario = get_user_model()


def crear_usuario(nombre, grupo=None, superusuario=False):
    usuario = Usuario.objects.create_user(
        username=nombre, password="clave-de-prueba", is_superuser=superusuario
    )
    if grupo:
        etiqueta, _ = Group.objects.get_or_create(name=grupo)
        usuario.groups.add(etiqueta)
    return usuario


@override_settings(REQUIERE_LOGIN=True)
class LoginObligatorio(TestCase):
    def test_anonimo_va_al_login(self):
        respuesta = self.client.get(reverse("home"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("login"), respuesta["Location"])
        self.assertIn("next=", respuesta["Location"])

    def test_anonimo_no_entra_a_ningun_modulo(self):
        for url in (
            reverse("miembros:lista"),
            reverse("eventos:lista"),
            reverse("inventario:lista"),
            reverse("reportes:indice"),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)

    def test_salud_es_publica(self):
        self.assertEqual(self.client.get(reverse("salud")).status_code, 200)

    def test_pantalla_de_login_se_ve(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

    def test_usuario_autenticado_entra(self):
        usuario = crear_usuario("lector", GRUPO_CONSULTA)
        self.client.force_login(usuario)
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)


class SinLoginObligatorio(TestCase):
    """Con REQUIERE_LOGIN=False (pruebas) no se restringe nada."""

    def test_anonimo_ve_la_portada(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_plantilla_muestra_los_formularios(self):
        respuesta = self.client.get(reverse("inventario:prestamos"))
        self.assertContains(respuesta, "Registrar préstamo")


@override_settings(REQUIERE_LOGIN=True)
class EscrituraPorRol(TestCase):
    def setUp(self):
        self.consulta = crear_usuario("consulta", GRUPO_CONSULTA)
        self.secretaria = crear_usuario("secretaria", GRUPO_SECRETARIA)
        self.inventario = crear_usuario("inventario", GRUPO_INVENTARIO)
        self.admin = crear_usuario("admin", GRUPO_ADMIN)

    def _post(self, usuario, url):
        self.client.force_login(usuario)
        return self.client.post(url, {})

    def test_consulta_puede_leer_pero_no_escribir(self):
        self.client.force_login(self.consulta)
        self.assertEqual(self.client.get(reverse("miembros:lista")).status_code, 200)

        respuesta = self.client.post(reverse("miembros:registrar"), {})
        self.assertEqual(respuesta.status_code, 403)
        self.assertContains(respuesta, "solo lectura", status_code=403)

    def test_secretaria_escribe_miembros_y_eventos(self):
        for url in (reverse("miembros:registrar"), reverse("eventos:registrar")):
            with self.subTest(url=url):
                respuesta = self._post(self.secretaria, url)
                self.assertNotEqual(respuesta.status_code, 403)

    def test_secretaria_no_escribe_inventario(self):
        respuesta = self._post(self.secretaria, reverse("inventario:registrar"))
        self.assertEqual(respuesta.status_code, 403)

    def test_encargado_de_inventario_escribe_solo_inventario(self):
        permitido = self._post(self.inventario, reverse("inventario:registrar"))
        self.assertNotEqual(permitido.status_code, 403)

        bloqueado = self._post(self.inventario, reverse("miembros:registrar"))
        self.assertEqual(bloqueado.status_code, 403)

    def test_admin_escribe_en_todos_los_modulos(self):
        for url in (
            reverse("miembros:registrar"),
            reverse("eventos:registrar"),
            reverse("inventario:registrar"),
        ):
            with self.subTest(url=url):
                respuesta = self._post(self.admin, url)
                self.assertNotEqual(respuesta.status_code, 403)


@override_settings(REQUIERE_LOGIN=True)
class EliminacionSoloAdmin(TestCase):
    def setUp(self):
        self.secretaria = crear_usuario("secretaria", GRUPO_SECRETARIA)
        self.admin = crear_usuario("admin", GRUPO_ADMIN)
        self.superusuario = crear_usuario("root", superusuario=True)

    def test_solo_el_admin_llega_a_la_vista_de_eliminar(self):
        # pk inexistente: si el middleware deja pasar, la vista responde 404;
        # si lo bloquea, responde 403 antes de buscar el registro.
        url = reverse("miembros:eliminar", args=[99999])

        self.client.force_login(self.secretaria)
        self.assertEqual(self.client.post(url).status_code, 403)

        for usuario in (self.admin, self.superusuario):
            with self.subTest(usuario=usuario.username):
                self.client.force_login(usuario)
                self.assertEqual(self.client.post(url).status_code, 404)
