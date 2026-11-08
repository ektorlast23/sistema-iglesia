"""Pruebas de integracion: los cuatro modulos encadenados por la interfaz web.

Las suites de las semanas 5-8 prueban cada app por separado. Aqui se recorre el
sistema como lo usaria la secretaria: registrar un miembro, crear un evento,
tomar asistencia, prestar un equipo y comprobar que todo aparece en los
reportes y en las descargas PDF/Excel.
"""

from datetime import timedelta

from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from eventos.models import Asistencia, Evento
from inventario.models import Prestamo
from miembros.models import Miembro
from reportes import consultas

from .base import BaseSistema


class FlujoMiembrosEventosReportes(BaseSistema):
    """Alta de miembro -> evento -> asistencia -> reporte -> exportacion."""

    def test_alta_miembro_evento_asistencia_reporte_y_pdf(self):
        # 1. Alta del miembro por la pantalla real.
        respuesta = self.client.post(
            reverse("miembros:registrar"), self.datos_miembro()
        )
        rosa = Miembro.objects.get(email="rosa@iglesia.test")
        self.assertRedirects(
            respuesta, reverse("miembros:detalle", args=[rosa.pk])
        )

        # 2. Alta del evento.
        respuesta = self.client.post(reverse("eventos:registrar"), self.datos_evento())
        self.assertRedirects(respuesta, reverse("eventos:lista"))
        vigilia = Evento.objects.get(nombre="Vigilia de oracion")

        # 3. Asistencia del miembro nuevo al evento nuevo.
        respuesta = self.client.post(
            reverse("eventos:asistencia_registrar", args=[vigilia.pk]),
            {
                "miembro": rosa.pk,
                "evento": vigilia.pk,
                "fecha": vigilia.fecha.isoformat(),
                "estado": "presente",
                "observaciones": "",
            },
        )
        self.assertRedirects(
            respuesta, reverse("eventos:detalle", args=[vigilia.pk])
        )
        self.assertEqual(Asistencia.objects.filter(evento=vigilia).count(), 1)

        # 4. El evento aparece en el reporte con su asistencia.
        respuesta = self.client.get(
            reverse("reportes:detalle", args=["asistencia"]),
            {"desde": "2026-11-01"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Vigilia de oracion")
        reporte = respuesta.context["reporte"]
        filas = {f[0]: f for f in reporte.secciones[0].filas}
        self.assertEqual(filas["Vigilia de oracion"][3], 1)  # presentes

        # 5. Descargas con el mismo contenido.
        pdf = self.client.get(reverse("reportes:exportar", args=["asistencia", "pdf"]))
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        self.assertIn("attachment", pdf["Content-Disposition"])

        xlsx = self.client.get(
            reverse("reportes:exportar", args=["asistencia", "xlsx"])
        )
        self.assertEqual(xlsx.status_code, 200)
        self.assertTrue(xlsx.content.startswith(b"PK"))

    def test_asistencia_duplicada_por_http_no_crea_segunda_fila(self):
        respuesta = self.client.post(
            reverse("eventos:asistencia_registrar", args=[self.culto.pk]),
            {
                "miembro": self.ana.pk,
                "evento": self.culto.pk,
                "fecha": self.culto.fecha.isoformat(),
                "estado": "presente",
                "observaciones": "",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "ya tiene asistencia registrada")
        self.assertEqual(
            Asistencia.objects.filter(miembro=self.ana, evento=self.culto).count(), 1
        )

    def test_cambio_de_estado_se_refleja_en_el_reporte(self):
        asistencia = Asistencia.objects.get(miembro=self.ana, evento=self.ensayo)
        respuesta = self.client.post(
            reverse("eventos:asistencia_editar", args=[asistencia.pk]),
            {"estado": "presente", "observaciones": "llego tarde pero asistio"},
        )
        self.assertRedirects(
            respuesta,
            reverse("eventos:lista_asistencias", args=[self.ensayo.pk]),
        )
        reporte = consultas.asistencia_por_evento()
        filas = {f[0]: f for f in reporte.secciones[0].filas}
        self.assertEqual(filas["Ensayo de alabanza"][3], 1)  # presentes
        self.assertEqual(filas["Ensayo de alabanza"][6], 0)  # retrasos

    def test_historial_por_miembro_solo_muestra_sus_eventos(self):
        respuesta = self.client.get(
            reverse("eventos:asistencia_consulta_miembro"),
            {"miembro_id": self.ana.pk},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Culto Dominical")
        self.assertContains(respuesta, "Ensayo de alabanza")
        self.assertEqual(len(respuesta.context["asistencias"]), 2)
        self.assertEqual(respuesta.context["miembro"], self.ana)
        # Carlos tambien tiene asistencia en el culto: no debe aparecer aqui.
        for asistencia in respuesta.context["asistencias"]:
            self.assertEqual(asistencia.miembro_id, self.ana.pk)

    def test_baja_logica_no_borra_y_la_saca_de_los_selectorables(self):
        respuesta = self.client.post(
            reverse("miembros:eliminar", args=[self.luis.pk])
        )
        self.assertRedirects(respuesta, reverse("miembros:lista"))

        luis = Miembro.objects.get(pk=self.luis.pk)  # la fila sigue existiendo
        self.assertEqual(luis.estado, "inactivo")

        # Ya no se puede elegir como responsable ni tomarle asistencia.
        from eventos.forms import AsistenciaForm, EventoForm

        self.assertNotIn(luis, EventoForm().fields["responsable"].queryset)
        self.assertNotIn(luis, AsistenciaForm().fields["miembro"].queryset)

        respuesta = self.client.post(
            reverse("eventos:asistencia_registrar", args=[self.culto.pk]),
            {
                "miembro": luis.pk,
                "evento": self.culto.pk,
                "fecha": self.culto.fecha.isoformat(),
                "estado": "presente",
            },
        )
        self.assertEqual(respuesta.status_code, 200)  # rechazado, no 302
        self.assertFalse(Asistencia.objects.filter(miembro=luis).exists())

    def test_evento_eliminado_arrastra_asistencias_y_sale_del_reporte(self):
        self.assertEqual(Asistencia.objects.filter(evento=self.ensayo).count(), 1)
        respuesta = self.client.post(
            reverse("eventos:eliminar", args=[self.ensayo.pk])
        )
        self.assertRedirects(respuesta, reverse("eventos:lista"))
        self.assertEqual(Asistencia.objects.filter(evento_id=self.ensayo.pk).count(), 0)

        reporte = consultas.asistencia_por_evento()
        nombres = [f[0] for f in reporte.secciones[0].filas]
        self.assertNotIn("Ensayo de alabanza", nombres)

    def test_miembro_con_prestamo_activo_no_se_puede_borrar(self):
        with self.assertRaises(ProtectedError):
            self.ana.delete()
        self.assertTrue(Miembro.objects.filter(pk=self.ana.pk).exists())
        self.assertEqual(Prestamo.objects.filter(estado="prestado").count(), 1)

    def test_alta_y_baja_se_ven_en_demografia(self):
        antes = consultas.demografia().resumen
        activos_antes = dict(antes)["Miembros activos"]

        self.client.post(reverse("miembros:registrar"), self.datos_miembro())
        activos_despues = dict(consultas.demografia().resumen)["Miembros activos"]
        self.assertEqual(activos_despues, activos_antes + 1)

        rosa = Miembro.objects.get(email="rosa@iglesia.test")
        self.client.post(reverse("miembros:eliminar", args=[rosa.pk]))
        activos_final = dict(consultas.demografia().resumen)["Miembros activos"]
        self.assertEqual(activos_final, activos_antes)

    def test_todas_las_pantallas_principales_responden(self):
        pantallas = [
            reverse("home"),
            reverse("miembros:lista"),
            reverse("miembros:registrar"),
            reverse("eventos:lista"),
            reverse("eventos:registrar"),
            reverse("inventario:lista"),
            reverse("inventario:registrar"),
            reverse("inventario:prestamos"),
            reverse("inventario:devoluciones"),
            reverse("reportes:indice"),
            reverse("reportes:detalle", args=["crecimiento"]),
            reverse("reportes:detalle", args=["inventario"]),
            reverse("reportes:detalle", args=["demografia"]),
        ]
        for url in pantallas:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class FlujoInventario(BaseSistema):
    """Prestamo -> reporte -> devolucion -> reporte."""

    def test_prestamo_devolucion_y_reporte_de_inventario(self):
        respuesta = self.client.post(
            reverse("inventario:prestamos"), self.datos_prestamo(cantidad=2)
        )
        self.assertRedirects(respuesta, reverse("inventario:prestamos"))

        self.guitarra.refresh_from_db()
        self.assertEqual(self.guitarra.cantidad_prestada, 3)  # 1 previo + 2 nuevos
        self.assertEqual(self.guitarra.cantidad_disponible, 0)

        reporte = consultas.inventario()
        filas = {f[0]: f for f in reporte.secciones[0].filas}
        self.assertIn("Instrumento", filas)
        self.assertEqual(filas["Instrumento"][2], 3)  # unidades totales
        self.assertEqual(filas["Instrumento"][3], 3)  # en prestamo
        self.assertEqual(filas["Instrumento"][4], 0)  # disponibles

        nuevo = Prestamo.objects.filter(miembro=self.carlos, estado="prestado").get()
        respuesta = self.client.post(
            reverse("inventario:devoluciones"), {"prestamo_id": nuevo.pk}
        )
        self.assertRedirects(respuesta, reverse("inventario:devoluciones"))

        nuevo.refresh_from_db()
        self.assertEqual(nuevo.estado, "devuelto")
        self.assertEqual(nuevo.fecha_devolucion_real, self.hoy)
        self.guitarra.refresh_from_db()
        self.assertEqual(self.guitarra.cantidad_disponible, 2)

    def test_no_se_puede_prestar_mas_de_lo_disponible(self):
        respuesta = self.client.post(
            reverse("inventario:prestamos"), self.datos_prestamo(cantidad=3)
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Solo hay 2 unidad")
        self.assertEqual(
            Prestamo.objects.filter(equipo=self.guitarra, estado="prestado").count(), 1
        )

    def test_equipo_de_baja_no_aparece_en_el_formulario_de_prestamo(self):
        respuesta = self.client.get(reverse("inventario:prestamos"))
        equipos = respuesta.context["form"].fields["equipo"].queryset
        self.assertIn(self.guitarra, equipos)
        self.assertIn(self.consola, equipos)  # en mantenimiento se puede prestar
        self.assertNotIn(self.proyector, equipos)  # de baja, no


class FlujoReportes(BaseSistema):
    """Descargas de los cuatro reportes en los dos formatos."""

    def test_los_cuatro_reportes_se_descangan_en_pdf_y_excel(self):
        for clave in ("asistencia", "crecimiento", "inventario", "demografia"):
            for formato, firma in (("pdf", b"%PDF"), ("xlsx", b"PK")):
                with self.subTest(clave=clave, formato=formato):
                    respuesta = self.client.get(
                        reverse("reportes:exportar", args=[clave, formato])
                    )
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertTrue(respuesta.content.startswith(firma))
                    self.assertGreater(len(respuesta.content), 1000)
                    self.assertIn(
                        f"reporte_{clave}_", respuesta["Content-Disposition"]
                    )
                    self.assertIn(f".{formato}", respuesta["Content-Disposition"])

    def test_filtros_de_fecha_afectan_pantalla_y_descarga(self):
        futuro = (self.hoy + timedelta(days=365)).isoformat()
        respuesta = self.client.get(
            reverse("reportes:detalle", args=["asistencia"]), {"desde": futuro}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["reporte"].vacio)

        pdf = self.client.get(
            reverse("reportes:exportar", args=["asistencia", "pdf"]),
            {"desde": futuro},
        )
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b"%PDF"))

    def test_reporte_inexistente_es_404(self):
        self.assertEqual(
            self.client.get(reverse("reportes:detalle", args=["no-existe"])).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                reverse("reportes:exportar", args=["no-existe", "pdf"])
            ).status_code,
            404,
        )
