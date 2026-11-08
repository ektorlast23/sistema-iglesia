"""Pruebas de rendimiento (Semana 9).

No son un benchmark: son guardas contra regresiones evidentes.

* Numero de consultas SQL por pantalla, que no debe crecer con la cantidad de
  filas (el clasico problema N+1).
* Tiempos de respuesta con umbrales muy holgados, para detectar solo fallos
  groseros (bucles infinitos, consultas sin indice, exportaciones gigantes).
* Existencia de indices en las claves foraneas que se filtran y ordenan.
"""

import time

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from eventos.models import Asistencia, Evento
from inventario.models import Equipo, Prestamo
from miembros.models import Miembro

from .base import BaseSistema


def contar_consultas(cliente, url, datos=None):
    """GET a una URL y devuelve (respuesta, numero de consultas)."""
    with CaptureQueriesContext(connection) as capturadas:
        respuesta = cliente.get(url, datos or {})
    return respuesta, len(capturadas)


class ConsultasConstantes(BaseSistema):
    """El numero de consultas no depende de cuantas filas haya."""

    def _miembros_extra(self, cuantos=30):
        Miembro.objects.bulk_create(
            [
                Miembro(
                    nombres=f"Miembro{indice}",
                    apellidos="De prueba",
                    estado="activo",
                    familia=self.familia,
                )
                for indice in range(cuantos)
            ]
        )

    def test_lista_de_miembros_no_crece_con_los_registros(self):
        url = reverse("miembros:lista")
        _, base = contar_consultas(self.client, url)
        self._miembros_extra(30)
        respuesta, despues = contar_consultas(self.client, url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Miembro29")
        self.assertEqual(despues, base, "la lista de miembros hace N+1")

    def test_lista_de_eventos_no_crece_con_los_registros(self):
        url = reverse("eventos:lista")
        _, base = contar_consultas(self.client, url)
        for indice in range(15):
            Evento.objects.create(
                nombre=f"Evento {indice}",
                fecha=self.hoy,
                responsable=self.ana,
            )
        respuesta, despues = contar_consultas(self.client, url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(despues, base, "la lista de eventos hace N+1")

    def test_lista_de_inventario_no_consulta_por_cada_equipo(self):
        # Regresion de la Semana 9: la plantilla muestra cantidad_disponible y
        # cada equipo lanzaba su propio SUM. Con prefetch son 2 consultas fijas.
        url = reverse("inventario:lista")
        _, base = contar_consultas(self.client, url)

        for indice in range(20):
            equipo = Equipo.objects.create(
                nombre=f"Equipo {indice}", categoria="recurso", cantidad=5
            )
            Prestamo.objects.create(
                equipo=equipo,
                miembro=self.ana,
                cantidad=2,
                fecha_prestamo=self.hoy,
                fecha_devolucion_prevista=self.hoy,
            )

        respuesta, despues = contar_consultas(self.client, url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(despues, base, "el listado de inventario hace N+1")
        self.assertLessEqual(despues, 3, "el listado deberia resolverse en 1-3 consultas")

    def test_la_disponibilidad_precargada_sigue_calculando_bien(self):
        # Las 20 consultas de la prueba anterior no deben romper el calculo.
        equipo = self.guitarra
        respuesta = self.client.get(reverse("inventario:lista"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(equipo.cantidad_prestada, 1)
        self.assertEqual(equipo.cantidad_disponible, 2)

        # La misma propiedad, sin precarga (acceso directo), da el mismo valor.
        suelto = Equipo.objects.get(pk=equipo.pk)
        self.assertEqual(suelto.cantidad_prestada, 1)
        self.assertEqual(suelto.cantidad_disponible, 2)

    def test_reporte_de_inventario_usa_agregados(self):
        url = reverse("reportes:detalle", args=["inventario"])
        _, base = contar_consultas(self.client, url)
        for indice in range(20):
            Equipo.objects.create(
                nombre=f"Equipo {indice}", categoria="mobiliario", cantidad=4
            )
        respuesta, despues = contar_consultas(self.client, url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(despues, base, "el reporte de inventario consulta por fila")

    def test_reporte_de_asistencia_usa_agregados(self):
        url = reverse("reportes:detalle", args=["asistencia"])
        _, base = contar_consultas(self.client, url)
        for indice in range(15):
            evento = Evento.objects.create(nombre=f"Evento {indice}", fecha=self.hoy)
            Asistencia.objects.create(
                miembro=self.ana, evento=evento, fecha=self.hoy, estado="presente"
            )
        respuesta, despues = contar_consultas(self.client, url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(despues, base, "el reporte de asistencia consulta por evento")

    def test_portada_no_toca_la_base(self):
        _, consultas = contar_consultas(self.client, reverse("home"))
        self.assertEqual(consultas, 0)


class TiemposDeRespuesta(BaseSistema):
    """Umbrales holgados: solo detectan problemas graves, no ruido del equipo."""

    def _medir(self, url, datos=None, repeticiones=3):
        tiempos = []
        for _ in range(repeticiones):
            inicio = time.perf_counter()
            respuesta = self.client.get(url, datos or {})
            tiempos.append(time.perf_counter() - inicio)
            self.assertEqual(respuesta.status_code, 200)
        return min(tiempos)  # el mejor tiempo reduce el ruido del sistema

    def test_pantallas_principales_bajo_el_umbral(self):
        pantallas = {
            "portada": reverse("home"),
            "miembros": reverse("miembros:lista"),
            "eventos": reverse("eventos:lista"),
            "inventario": reverse("inventario:lista"),
            "prestamos": reverse("inventario:prestamos"),
            "reportes": reverse("reportes:indice"),
        }
        for nombre, url in pantallas.items():
            with self.subTest(pantalla=nombre):
                self.assertLess(self._medir(url), 2.0, f"{nombre} tarda demasiado")

    def test_reportes_bajo_el_umbral(self):
        for clave in ("asistencia", "crecimiento", "inventario", "demografia"):
            with self.subTest(reporte=clave):
                url = reverse("reportes:detalle", args=[clave])
                self.assertLess(self._medir(url), 2.0)

    def test_exportaciones_bajo_el_umbral(self):
        for clave in ("asistencia", "crecimiento", "inventario", "demografia"):
            for formato in ("pdf", "xlsx"):
                with self.subTest(reporte=clave, formato=formato):
                    url = reverse("reportes:exportar", args=[clave, formato])
                    inicio = time.perf_counter()
                    respuesta = self.client.get(url)
                    duracion = time.perf_counter() - inicio
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertLess(duracion, 5.0, "la exportacion tarda demasiado")

    def test_la_busqueda_no_degradacion_con_texto_largo(self):
        # icontains con un texto largo no debe volverse cuadratico.
        self._miembros_extra(50)
        inicio = time.perf_counter()
        respuesta = self.client.get(
            reverse("miembros:lista"), {"q": "miembro" * 20}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertLess(time.perf_counter() - inicio, 2.0)

    def _miembros_extra(self, cuantos):
        Miembro.objects.bulk_create(
            [
                Miembro(nombres=f"Persona{indice}", apellidos="Carga", estado="activo")
                for indice in range(cuantos)
            ]
        )


class IndicesDeClavesForaneas(TestCase):
    """Toda FK por la que se filtra u ordena debe tener su indice."""

    def _indices(self, tabla):
        with connection.cursor() as cursor:
            return connection.introspection.get_constraints(cursor, tabla)

    def _tiene_indice(self, tabla, columna):
        for datos in self._indices(tabla).values():
            if datos.get("index") and datos.get("columns") and datos["columns"][0] == columna:
                return True
        return False

    def test_claves_foraneas_de_asistencia(self):
        self.assertTrue(self._tiene_indice("asistencias", "miembro_id"))
        self.assertTrue(self._tiene_indice("asistencias", "evento_id"))

    def test_claves_foraneas_de_prestamos(self):
        self.assertTrue(self._tiene_indice("prestamos", "equipo_id"))
        self.assertTrue(self._tiene_indice("prestamos", "miembro_id"))

    def test_claves_foraneas_de_miembros_y_eventos(self):
        self.assertTrue(self._tiene_indice("miembros", "familia_id"))
        self.assertTrue(self._tiene_indice("eventos", "responsable_id"))

    # Nota: ademas de estos indices (que Django crea en cualquier motor), el
    # esquema MySQL agrega idx_eventos_fecha, idx_asistencias_fecha,
    # idx_miembros_estado e idx_asistencias_evento desde
    # modelo_iglesia_cursor_demo.sql; estan verificados en la evidencia
    # 05_RENDIMIENTO/indices_mysql.txt.
