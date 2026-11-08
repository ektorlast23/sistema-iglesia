"""Control de errores (Semana 9): 404, 400, 405 y envios invalidos.

El objetivo es que un error del usuario nunca se convierta en una pantalla de
fallo del servidor: id inexistente, texto donde va un numero, formulario
incompleto o metodo HTTP equivocado deben responder con un codigo controlado.
"""

from django.test import TestCase
from django.urls import reverse

from eventos.models import Asistencia, Evento
from inventario.models import Equipo, Prestamo
from miembros.models import Miembro

from .base import BaseSistema


class RecursoInexistente(BaseSistema):
    """Todo id que no exista responde 404, en los cuatro modulos."""

    def test_miembros(self):
        for nombre in ("miembros:detalle", "miembros:editar", "miembros:eliminar"):
            with self.subTest(vista=nombre):
                respuesta = self.client.get(reverse(nombre, args=[99999]))
                self.assertEqual(respuesta.status_code, 404)

    def test_eventos(self):
        for nombre in ("eventos:detalle", "eventos:editar", "eventos:eliminar"):
            with self.subTest(vista=nombre):
                respuesta = self.client.get(reverse(nombre, args=[99999]))
                self.assertEqual(respuesta.status_code, 404)

    def test_asistencias_de_un_evento_inexistente(self):
        for nombre in ("eventos:asistencia_registrar", "eventos:lista_asistencias"):
            with self.subTest(vista=nombre):
                respuesta = self.client.get(reverse(nombre, args=[99999]))
                self.assertEqual(respuesta.status_code, 404)

    def test_editar_una_asistencia_inexistente(self):
        respuesta = self.client.get(
            reverse("eventos:asistencia_editar", args=[99999])
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_inventario(self):
        for nombre in ("inventario:detalle", "inventario:editar"):
            with self.subTest(vista=nombre):
                respuesta = self.client.get(reverse(nombre, args=[99999]))
                self.assertEqual(respuesta.status_code, 404)


class EntradasInvalidas(BaseSistema):
    """Un id que no es numero responde 404, no 500."""

    def test_devolucion_con_id_de_texto(self):
        respuesta = self.client.post(
            reverse("inventario:devoluciones"), {"prestamo_id": "abc"}
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_devolucion_sin_id(self):
        respuesta = self.client.post(reverse("inventario:devoluciones"), {})
        self.assertEqual(respuesta.status_code, 404)

    def test_devolucion_con_id_inexistente(self):
        respuesta = self.client.post(
            reverse("inventario:devoluciones"), {"prestamo_id": 99999}
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_devolucion_de_un_prestamo_ya_devuelto(self):
        self.prestamo.estado = "devuelto"
        self.prestamo.save(update_fields=["estado"])
        respuesta = self.client.post(
            reverse("inventario:devoluciones"), {"prestamo_id": self.prestamo.pk},
            follow=True,
        )
        self.assertContains(respuesta, "ya estaba devuelto")
        self.prestamo.refresh_from_db()
        self.assertEqual(self.prestamo.estado, "devuelto")

    def test_historial_con_miembro_de_texto(self):
        respuesta = self.client.get(
            reverse("eventos:asistencia_consulta_miembro"), {"miembro_id": "ana"}
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_historial_de_un_miembro_inexistente(self):
        respuesta = self.client.get(
            reverse("eventos:asistencia_consulta_miembro"), {"miembro_id": 99999}
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_historial_sin_parametro_muestra_el_selector(self):
        respuesta = self.client.get(reverse("eventos:asistencia_consulta_miembro"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertIsNone(respuesta.context["miembro"])
        self.assertEqual(len(respuesta.context["asistencias"]), 0)

    def test_filtro_de_fecha_invalido_se_ignora(self):
        respuesta = self.client.get(
            reverse("reportes:detalle", args=["asistencia"]),
            {"desde": "ayer", "hasta": "13/13/2026"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["reporte"].filtros == {})
        self.assertEqual(
            len(respuesta.context["reporte"].secciones[0].filas), 2  # dos eventos
        )


class MetodosYFormatos(BaseSistema):
    def test_post_a_la_portada_no_esta_permitido(self):
        respuesta = self.client.post(reverse("home"), {})
        self.assertEqual(respuesta.status_code, 405)

    def test_formato_de_exportacion_no_soportado(self):
        for formato in ("csv", "docx", "PDF"):
            with self.subTest(formato=formato):
                respuesta = self.client.get(
                    reverse("reportes:exportar", args=["asistencia", formato])
                )
                self.assertEqual(respuesta.status_code, 400)

    def test_tipo_de_evento_inexistente_da_reporte_vacio(self):
        respuesta = self.client.get(
            reverse("reportes:detalle", args=["asistencia"]),
            {"tipo": "concierto"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["reporte"].vacio)


class EnviosInvalidosNoEscriben(BaseSistema):
    """Un POST con errores vuelve al formulario (200) y no crea filas."""

    def test_miembro_sin_nombre(self):
        antes = Miembro.objects.count()
        respuesta = self.client.post(
            reverse("miembros:registrar"),
            {"nombres": "", "apellidos": "Mejia", "estado": "activo"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Revisa los errores del formulario")
        self.assertEqual(Miembro.objects.count(), antes)

    def test_evento_con_horas_invertidas(self):
        antes = Evento.objects.count()
        respuesta = self.client.post(
            reverse("eventos:registrar"),
            self.datos_evento(hora_inicio="21:00", hora_fin="19:00"),
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Evento.objects.count(), antes)

    def test_equipo_con_cantidad_cero(self):
        antes = Equipo.objects.count()
        respuesta = self.client.post(
            reverse("inventario:registrar"),
            {
                "nombre": "Micrófono",
                "categoria": "sonido",
                "cantidad": 0,
                "estado": "disponible",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Equipo.objects.count(), antes)

    def test_prestamo_que_excede_existencias(self):
        antes = Prestamo.objects.count()
        respuesta = self.client.post(
            reverse("inventario:prestamos"), self.datos_prestamo(cantidad=99)
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Solo hay 2 unidad")
        self.assertEqual(Prestamo.objects.count(), antes)

    def test_asistencia_con_miembro_inactivo(self):
        antes = Asistencia.objects.count()
        respuesta = self.client.post(
            reverse("eventos:asistencia_registrar", args=[self.culto.pk]),
            {
                "miembro": self.marta.pk,
                "evento": self.culto.pk,
                "fecha": self.culto.fecha.isoformat(),
                "estado": "presente",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Asistencia.objects.count(), antes)
