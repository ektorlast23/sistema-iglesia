"""Pruebas del módulo de reportes (Semana 8, viernes).

Cubren las consultas agregadas de los cuatro reportes, su presentación en
pantalla y la exportación a PDF/Excel. Se ejecutan sobre SQLite en memoria
(ver config/settings.py, bloque de test).
"""

from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from eventos.models import Asistencia, Evento
from inventario.models import Equipo, Prestamo
from miembros.models import Familia, Miembro, MiembroMinisterio, Ministerio

from . import consultas
from .exportar import exportar_pdf, exportar_xlsx


class BaseReportes(TestCase):
    def setUp(self):
        self.familia = Familia.objects.create(nombre_familia="Hernández")
        self.alabanza = Ministerio.objects.create(nombre="Alabanza")
        self.sonido = Ministerio.objects.create(nombre="Sonido")

        self.ana = Miembro.objects.create(
            nombres="Ana", apellidos="Hernández", sexo="F",
            fecha_nacimiento=date(1990, 5, 10), estado="activo", familia=self.familia,
        )
        self.carlos = Miembro.objects.create(
            nombres="Carlos", apellidos="Hernández", sexo="M",
            fecha_nacimiento=date(1975, 3, 2), estado="activo", familia=self.familia,
        )
        self.luis = Miembro.objects.create(
            nombres="Luis", apellidos="Ramírez", sexo="M",
            fecha_nacimiento=date(2010, 1, 15), estado="visitante",
        )
        MiembroMinisterio.objects.create(miembro=self.ana, ministerio=self.alabanza)
        MiembroMinisterio.objects.create(miembro=self.carlos, ministerio=self.alabanza)
        MiembroMinisterio.objects.create(miembro=self.carlos, ministerio=self.sonido)

        self.culto = Evento.objects.create(
            nombre="Culto Dominical", fecha=date(2026, 10, 4), tipo="culto"
        )
        self.ensayo = Evento.objects.create(
            nombre="Ensayo de alabanza", fecha=date(2026, 10, 10), tipo="ensayo"
        )
        self.culto_nov = Evento.objects.create(
            nombre="Culto Dominical", fecha=date(2026, 11, 1), tipo="culto"
        )

        Asistencia.objects.create(miembro=self.ana, evento=self.culto,
                                  fecha=self.culto.fecha, estado="presente")
        Asistencia.objects.create(miembro=self.carlos, evento=self.culto,
                                  fecha=self.culto.fecha, estado="presente")
        Asistencia.objects.create(miembro=self.luis, evento=self.culto,
                                  fecha=self.culto.fecha, estado="ausente")
        Asistencia.objects.create(miembro=self.carlos, evento=self.ensayo,
                                  fecha=self.ensayo.fecha, estado="presente")
        Asistencia.objects.create(miembro=self.ana, evento=self.culto_nov,
                                  fecha=self.culto_nov.fecha, estado="presente")
        Asistencia.objects.create(miembro=self.carlos, evento=self.culto_nov,
                                  fecha=self.culto_nov.fecha, estado="justificado")

        self.microfono = Equipo.objects.create(
            nombre="Micrófono", categoria="sonido", cantidad=4, estado="disponible"
        )
        self.guitarra = Equipo.objects.create(
            nombre="Guitarra", categoria="instrumento", cantidad=2, estado="mantenimiento"
        )
        self.silla = Equipo.objects.create(
            nombre="Silla", categoria="mobiliario", cantidad=10, estado="baja"
        )

        hoy = timezone.localdate()
        Prestamo.objects.create(
            equipo=self.microfono, miembro=self.ana, cantidad=1,
            fecha_prestamo=hoy - timedelta(days=10),
            fecha_devolucion_prevista=hoy - timedelta(days=3), estado="prestado",
        )
        Prestamo.objects.create(
            equipo=self.microfono, miembro=self.carlos, cantidad=1,
            fecha_prestamo=hoy - timedelta(days=20),
            fecha_devolucion_prevista=hoy - timedelta(days=15), estado="devuelto",
        )
        Prestamo.objects.create(
            equipo=self.guitarra, miembro=self.carlos, cantidad=1,
            fecha_prestamo=hoy - timedelta(days=2),
            fecha_devolucion_prevista=hoy + timedelta(days=5), estado="prestado",
        )


# ------------------------------------------------------------ 1. asistencia
class AsistenciaPorEventoTests(BaseReportes):
    def test_cuenta_estados_por_evento(self):
        r = consultas.asistencia_por_evento()
        filas = r.secciones[0].filas
        self.assertEqual(len(filas), 3)
        culto = next(f for f in filas if f[1] == "04/10/2026")
        self.assertEqual(culto[0], "Culto Dominical")
        self.assertEqual(culto[3:8], [2, 1, 0, 0, 3])
        self.assertEqual(culto[8], "66.7 %")

    def test_resumen_suma_asistencias_y_promedio(self):
        r = dict(consultas.asistencia_por_evento().resumen)
        self.assertEqual(r["Eventos en el periodo"], 3)
        self.assertEqual(r["Asistencias registradas"], 6)
        self.assertEqual(r["Asistencias presentes"], 4)
        self.assertEqual(r["Promedio de presentes por evento"], 1.3)

    def test_ordena_del_evento_mas_reciente_al_mas_antiguo(self):
        fechas = [f[1] for f in consultas.asistencia_por_evento().secciones[0].filas]
        self.assertEqual(fechas, ["01/11/2026", "10/10/2026", "04/10/2026"])

    def test_filtra_por_rango_de_fechas(self):
        r = consultas.asistencia_por_evento(desde=date(2026, 10, 5))
        self.assertEqual(len(r.secciones[0].filas), 2)
        r = consultas.asistencia_por_evento(hasta=date(2026, 10, 31))
        self.assertEqual(len(r.secciones[0].filas), 2)

    def test_filtra_por_tipo(self):
        r = consultas.asistencia_por_evento(tipo="ensayo")
        filas = r.secciones[0].filas
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0][0], "Ensayo de alabanza")

    def test_evento_sin_asistencias_aparece_con_ceros(self):
        Evento.objects.create(nombre="Vigilia", fecha=date(2026, 12, 24), tipo="vigilia")
        r = consultas.asistencia_por_evento(tipo="vigilia")
        self.assertEqual(r.secciones[0].filas[0][3:8], [0, 0, 0, 0, 0])
        self.assertEqual(r.secciones[0].filas[0][8], "0.0 %")

    def test_sin_eventos_no_falla(self):
        Evento.objects.all().delete()
        r = consultas.asistencia_por_evento()
        self.assertEqual(r.secciones[0].filas, [])
        self.assertEqual(dict(r.resumen)["Eventos en el periodo"], 0)


# ------------------------------------------------------------ 2. crecimiento
class CrecimientoTests(BaseReportes):
    def test_agrupa_por_mes(self):
        r = consultas.crecimiento_asistencia()
        filas = r.secciones[0].filas
        self.assertEqual([f[0] for f in filas], ["10/2026", "11/2026"])
        self.assertEqual(filas[0][1:4], [2, 4, 3])
        self.assertEqual(filas[0][4], "75.0 %")

    def test_calcula_presentes_por_evento(self):
        filas = consultas.crecimiento_asistencia().secciones[0].filas
        self.assertEqual(filas[0][5], 1.5)
        self.assertEqual(filas[1][5], 1.0)

    def test_variacion_del_ultimo_mes(self):
        r = dict(consultas.crecimiento_asistencia().resumen)
        self.assertEqual(r["Variación del último mes"], "-66.7 %")

    def test_ranking_de_eventos_mas_concurridos(self):
        filas = consultas.crecimiento_asistencia().secciones[1].filas
        self.assertEqual(filas[0][1], "Culto Dominical")
        self.assertEqual(filas[0][4], 2)
        self.assertEqual(len(filas), 3)

    def test_filtra_crecimiento_por_fechas(self):
        r = consultas.crecimiento_asistencia(desde=date(2026, 11, 1))
        self.assertEqual(len(r.secciones[0].filas), 1)
        self.assertEqual(r.secciones[0].filas[0][0], "11/2026")


# ------------------------------------------------------------- 3. inventario
class InventarioTests(BaseReportes):
    def _fila(self, categoria):
        r = consultas.inventario()
        return next(f for f in r.secciones[0].filas if f[0] == categoria)

    def test_disponibilidad_por_categoria(self):
        sonido = self._fila("Sonido")
        self.assertEqual(sonido[1:], [1, 4, 1, 3, 0, 0])

    def test_mantenimiento_y_baja_no_se_prestan(self):
        guitarra = self._fila("Instrumento")
        self.assertEqual(guitarra[4], 1)   # 2 unidades - 1 prestada
        self.assertEqual(guitarra[5], 2)   # en mantenimiento
        silla = self._fila("Mobiliario")
        self.assertEqual(silla[4], 0)      # de baja: nada disponible

    def test_prestamo_devuelto_no_descuenta(self):
        self.assertEqual(self._fila("Sonido")[3], 1)

    def test_resumen_y_atrasados(self):
        r = dict(consultas.inventario().resumen)
        self.assertEqual(r["Equipos registrados"], 3)
        self.assertEqual(r["Unidades totales"], 16)
        self.assertEqual(r["Préstamos activos"], 2)
        self.assertEqual(r["Préstamos atrasados"], 1)

    def test_lista_prestamos_activos_con_situacion(self):
        filas = consultas.inventario().secciones[1].filas
        self.assertEqual(len(filas), 2)
        self.assertTrue(any("Atrasado" in f[5] for f in filas))
        self.assertTrue(any(f[5] == "En plazo" for f in filas))


# ------------------------------------------------------------- 4. demografía
class DemografiaTests(BaseReportes):
    def _seccion(self, titulo):
        return next(s for s in consultas.demografia().secciones if s.titulo == titulo)

    def test_por_estado(self):
        filas = dict((f[0], f[1]) for f in self._seccion("Por estado").filas)
        self.assertEqual(filas, {"Activo": 2, "Visitante": 1})

    def test_por_sexo(self):
        filas = dict((f[0], f[1]) for f in self._seccion("Por sexo").filas)
        self.assertEqual(filas, {"Masculino": 2, "Femenino": 1})

    def test_rangos_de_edad(self):
        filas = dict((f[0], f[1]) for f in self._seccion("Por rango de edad").filas)
        self.assertEqual(filas["Menores de 18"], 1)
        self.assertEqual(filas["36 a 45 años"], 1)
        self.assertEqual(filas["46 a 60 años"], 1)

    def test_familias_y_ministerios(self):
        familias = dict((f[0], f[1]) for f in self._seccion("Familias con más miembros").filas)
        self.assertEqual(familias, {"Hernández": 2, "Sin familia": 1})
        ministerios = dict((f[0], f[1]) for f in self._seccion("Participación por ministerio").filas)
        self.assertEqual(ministerios["Alabanza"], 2)
        self.assertEqual(ministerios["Sonido"], 1)

    def test_resumen(self):
        r = dict(consultas.demografia().resumen)
        self.assertEqual(r["Miembros registrados"], 3)
        self.assertEqual(r["Miembros activos"], 2)
        self.assertEqual(r["Miembros con familia asignada"], 2)
        self.assertEqual(r["Miembros en algún ministerio"], 2)

    def test_base_vacia_no_falla(self):
        Prestamo.objects.all().delete()
        Miembro.objects.all().delete()
        Materializados = consultas.demografia()
        self.assertEqual(len(Materializados.secciones), 5)
        self.assertEqual(dict(Materializados.resumen)["Miembros registrados"], 0)


# ------------------------------------------------------------------- vistas
class VistasTests(BaseReportes):
    def test_indice(self):
        respuesta = self.client.get(reverse("reportes:indice"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Reportes y estadísticas")
        self.assertContains(respuesta, "Crecimiento de la asistencia")

    def test_detalle_de_cada_reporte(self):
        for clave in consultas.CATALOGO:
            respuesta = self.client.get(reverse("reportes:detalle", args=[clave]))
            self.assertEqual(respuesta.status_code, 200, clave)

    def test_detalle_muestra_los_datos(self):
        respuesta = self.client.get(reverse("reportes:detalle", args=["asistencia"]))
        self.assertContains(respuesta, "Culto Dominical")
        self.assertContains(respuesta, "66.7 %")

    def test_detalle_respeta_filtros(self):
        respuesta = self.client.get(
            reverse("reportes:detalle", args=["asistencia"]),
            {"desde": "2026-11-01"},
        )
        self.assertContains(respuesta, "01/11/2026")
        self.assertNotContains(respuesta, "04/10/2026")

    def test_clave_inexistente_devuelve_404(self):
        respuesta = self.client.get(reverse("reportes:detalle", args=["no-existe"]))
        self.assertEqual(respuesta.status_code, 404)

    def test_exportar_pdf(self):
        respuesta = self.client.get(reverse("reportes:exportar", args=["asistencia", "pdf"]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "application/pdf")
        self.assertTrue(respuesta.content.startswith(b"%PDF"))
        self.assertIn("reporte_asistencia_", respuesta["Content-Disposition"])

    def test_exportar_excel(self):
        respuesta = self.client.get(reverse("reportes:exportar", args=["inventario", "xlsx"]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(respuesta.content.startswith(b"PK"))
        self.assertIn(".xlsx", respuesta["Content-Disposition"])

    def test_exportar_formato_invalido(self):
        respuesta = self.client.get(reverse("reportes:exportar", args=["asistencia", "csv"]))
        self.assertEqual(respuesta.status_code, 400)

    def test_exportar_los_cuatro_reportes(self):
        """Cada reporte debe salir en PDF y Excel: son tablas de distinto ancho."""
        for clave in consultas.CATALOGO:
            pdf = self.client.get(reverse("reportes:exportar", args=[clave, "pdf"]))
            self.assertEqual(pdf.status_code, 200, clave)
            self.assertTrue(pdf.content.startswith(b"%PDF"), clave)
            xlsx = self.client.get(reverse("reportes:exportar", args=[clave, "xlsx"]))
            self.assertEqual(xlsx.status_code, 200, clave)
            self.assertTrue(xlsx.content.startswith(b"PK"), clave)

    def test_exportar_clave_inexistente(self):
        respuesta = self.client.get(reverse("reportes:exportar", args=["no-existe", "pdf"]))
        self.assertEqual(respuesta.status_code, 404)

    def test_exportar_pdf_respeta_filtros(self):
        respuesta = self.client.get(
            reverse("reportes:exportar", args=["crecimiento", "pdf"]),
            {"desde": "2026-11-01"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertGreater(len(respuesta.content), 1000)


# --------------------------------------------------- exportación sin datos
class ExportacionVaciaTests(TestCase):
    def test_pdf_de_base_vacia(self):
        contenido = exportar_pdf(consultas.demografia())
        self.assertTrue(contenido.startswith(b"%PDF"))

    def test_excel_de_base_vacia(self):
        contenido = exportar_xlsx(consultas.asistencia_por_evento())
        self.assertTrue(contenido.startswith(b"PK"))
