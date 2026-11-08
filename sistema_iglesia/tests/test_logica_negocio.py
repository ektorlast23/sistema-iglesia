"""Verificacion de la logica de negocio (Semana 9).

Reglas que el sistema promete y que ninguna pantalla deberia poder romper:

* la disponibilidad de un equipo se calcula (total - prestamos activos - bajas);
* un prestamo sabe si esta activo y si esta atrasado;
* los borrados respetan las relaciones (SET_NULL, PROTECT, CASCADE);
* los duplicados que el modelo prohibe (unique_together) no entran;
* los agregados de los reportes (porcentajes, rangos de edad, totales) cuadran.
"""

from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from eventos.models import Asistencia, Evento
from inventario.models import Equipo, Prestamo
from miembros.models import Familia, Miembro, MiembroMinisterio, Ministerio
from reportes import consultas
from reportes.consultas import RANGOS_EDAD, Reporte, Seccion
from reportes.exportar import nombre_archivo

from .base import BaseSistema, nacido


class DisponibilidadCalculada(BaseSistema):
    """La disponibilidad no se guarda: se deriva de los prestamos activos."""

    def test_disponible_es_total_menos_prestado(self):
        self.assertEqual(self.guitarra.cantidad, 3)
        self.assertEqual(self.guitarra.cantidad_prestada, 1)
        self.assertEqual(self.guitarra.cantidad_disponible, 2)
        self.assertTrue(self.guitarra.disponible)

    def test_varios_prestamos_se_suman(self):
        Prestamo.objects.create(
            equipo=self.guitarra,
            miembro=self.carlos,
            cantidad=2,
            fecha_prestamo=self.hoy,
            fecha_devolucion_prevista=self.hoy + timedelta(days=3),
        )
        self.assertEqual(self.guitarra.cantidad_prestada, 3)
        self.assertEqual(self.guitarra.cantidad_disponible, 0)
        self.assertFalse(self.guitarra.disponible)

    def test_un_prestamo_devuelto_deja_de_contar(self):
        self.prestamo.estado = "devuelto"
        self.prestamo.fecha_devolucion_real = self.hoy
        self.prestamo.save()
        self.assertEqual(self.guitarra.cantidad_prestada, 0)
        self.assertEqual(self.guitarra.cantidad_disponible, 3)

    def test_nunca_baja_de_cero(self):
        # Aunque se registre de mas, la propiedad no devuelve negativos.
        Prestamo.objects.create(
            equipo=self.guitarra,
            miembro=self.carlos,
            cantidad=10,
            fecha_prestamo=self.hoy,
            fecha_devolucion_prevista=self.hoy + timedelta(days=1),
        )
        self.assertEqual(self.guitarra.cantidad_disponible, 0)

    def test_equipo_de_baja_no_tiene_disponibles(self):
        self.assertEqual(self.proyector.cantidad, 2)
        self.assertEqual(self.proyector.cantidad_disponible, 0)
        self.assertFalse(self.proyector.disponible)

    def test_equipo_en_mantenimiento_sigue_prestables(self):
        # Regla del sistema: mantenimiento no bloquea el prestamo; la baja si.
        self.assertTrue(self.consola.disponible)
        self.assertEqual(self.consola.cantidad_disponible, 1)


class SituacionDelPrestamo(BaseSistema):
    def test_activo_mientras_no_se_devuelva(self):
        self.assertTrue(self.prestamo.activo)
        self.prestamo.estado = "devuelto"
        self.assertFalse(self.prestamo.activo)

    def test_atrasado_solo_si_la_fecha_ya_paso(self):
        self.assertFalse(self.prestamo.atrasado)  # vence en 5 dias

        self.prestamo.fecha_devolucion_prevista = self.hoy - timedelta(days=1)
        self.prestamo.save()
        self.assertTrue(self.prestamo.atrasado)

    def test_un_prestamo_devuelto_no_esta_atrasado(self):
        self.prestamo.fecha_devolucion_prevista = self.hoy - timedelta(days=30)
        self.prestamo.estado = "devuelto"
        self.prestamo.save()
        self.assertFalse(self.prestamo.atrasado)

    def test_vencer_hoy_no_es_atraso(self):
        self.prestamo.fecha_devolucion_prevista = self.hoy
        self.prestamo.save()
        self.assertFalse(self.prestamo.atrasado)


class BorradosYRelaciones(BaseSistema):
    """Que pasa con las filas relacionadas al borrar."""

    def test_borrar_la_familia_deja_a_los_miembros_sin_familia(self):
        self.familia.delete()
        self.ana.refresh_from_db()
        self.carlos.refresh_from_db()
        self.assertIsNone(self.ana.familia_id)
        self.assertIsNone(self.carlos.familia_id)
        self.assertTrue(Miembro.objects.filter(pk=self.ana.pk).exists())

    def test_borrar_un_evento_arrastra_sus_asistencias(self):
        self.ensayo.delete()
        self.assertFalse(
            Asistencia.objects.filter(evento_id=self.ensayo.pk).exists()
        )
        # Las asistencias del otro evento siguen intactas.
        self.assertEqual(Asistencia.objects.filter(evento=self.culto).count(), 2)

    def test_borrar_un_equipo_arrastra_sus_prestamos(self):
        self.guitarra.delete()
        self.assertFalse(Prestamo.objects.filter(equipo_id=self.guitarra.pk).exists())

    def test_no_se_borra_un_miembro_con_prestamos(self):
        with self.assertRaises(ProtectedError):
            self.ana.delete()
        self.assertTrue(Miembro.objects.filter(pk=self.ana.pk).exists())

    def test_borrar_un_miembro_sin_prestamos_arrastra_sus_asistencias(self):
        self.assertEqual(Asistencia.objects.filter(miembro=self.luis).count(), 0)
        self.luis.delete()
        self.assertFalse(Miembro.objects.filter(pk=self.luis.pk).exists())

    def test_un_miembro_con_asistencias_pero_sin_prestamos_se_puede_borrar(self):
        # Carlos no tiene prestamos: PROTECT no aplica y sus asistencias caen.
        self.carlos.delete()
        self.assertFalse(Asistencia.objects.filter(miembro_id=self.carlos.pk).exists())


class DuplicadosProhibidos(BaseSistema):
    """Restricciones de unicidad del modelo, no solo del formulario."""

    def test_un_miembro_no_se_repite_en_el_mismo_ministerio(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            MiembroMinisterio.objects.create(
                miembro=self.ana, ministerio=self.alabanza
            )

    def test_un_miembro_no_tiene_dos_asistencias_en_el_mismo_evento(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Asistencia.objects.create(
                miembro=self.ana,
                evento=self.culto,
                fecha=self.culto.fecha,
                estado="presente",
            )

    def test_el_mismo_miembro_si_puede_estar_en_dos_ministerios(self):
        MiembroMinisterio.objects.create(miembro=self.ana, ministerio=self.jovenes)
        self.assertEqual(self.ana.ministerios.count(), 2)

    def test_el_nombre_de_la_familia_es_unico(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Familia.objects.create(nombre_familia="Hernandez")


class AgregadosDeReportes(BaseSistema):
    """Los numeros que muestran PDF, Excel y pantalla salen de las mismas reglas."""

    def test_inventario_cuadra_por_categoria(self):
        reporte = consultas.inventario()
        filas = {f[0]: f for f in reporte.secciones[0].filas}

        instrumento = filas["Instrumento"]
        self.assertEqual(instrumento[1], 1)  # equipos
        self.assertEqual(instrumento[2], 3)  # unidades
        self.assertEqual(instrumento[3], 1)  # en prestamo
        self.assertEqual(instrumento[4], 2)  # disponibles

        sonido = filas["Sonido"]
        self.assertEqual(sonido[5], 1)  # en mantenimiento

        recurso = filas["Recurso"]
        self.assertEqual(recurso[6], 2)  # de baja
        self.assertEqual(recurso[4], 0)  # disponibles

        # Las cuatro categorias siempre se listan, aunque esten vacias.
        self.assertEqual(len(filas), 4)
        self.assertEqual(filas["Mobiliario"][1:], [0, 0, 0, 0, 0, 0])

    def test_inventario_resumen_suma_las_filas(self):
        resumen = dict(consultas.inventario().resumen)
        self.assertEqual(resumen["Equipos registrados"], 3)
        self.assertEqual(resumen["Unidades totales"], 6)
        self.assertEqual(resumen["Unidades en préstamo"], 1)
        self.assertEqual(resumen["Unidades disponibles"], 3)
        self.assertEqual(resumen["Préstamos activos"], 1)
        self.assertEqual(resumen["Préstamos atrasados"], 0)

    def test_inventario_marca_el_prestamo_atrasado(self):
        self.prestamo.fecha_devolucion_prevista = self.hoy - timedelta(days=4)
        self.prestamo.save()

        reporte = consultas.inventario()
        self.assertEqual(dict(reporte.resumen)["Préstamos atrasados"], 1)
        fila = reporte.secciones[1].filas[0]
        self.assertEqual(fila[0], "Guitarra acustica")
        self.assertIn("Atrasado 4 día", fila[5])

    def test_asistencia_por_evento_desglosa_y_porcentua(self):
        reporte = consultas.asistencia_por_evento()
        filas = {f[0]: f for f in reporte.secciones[0].filas}

        culto = filas["Culto Dominical"]
        self.assertEqual(culto[3], 1)  # presentes
        self.assertEqual(culto[4], 1)  # ausentes
        self.assertEqual(culto[7], 2)  # total
        self.assertEqual(culto[8], "50.0 %")

        ensayo = filas["Ensayo de alabanza"]
        self.assertEqual(ensayo[6], 1)  # retrasos
        self.assertEqual(ensayo[8], "0.0 %")  # ningun presente

    def test_crecimiento_agrupa_por_mes(self):
        reporte = consultas.crecimiento_asistencia()
        meses = reporte.secciones[0].filas
        # Un renglon por mes calendario con eventos (el escenario puede caer en
        # dos meses si la semana de hoy cruza el cambio de mes).
        etiquetas = {f"{e.fecha:%m/%Y}" for e in (self.culto, self.ensayo)}
        self.assertEqual({f[0] for f in meses}, etiquetas)
        self.assertEqual(sum(f[1] for f in meses), 2)  # eventos
        self.assertEqual(sum(f[2] for f in meses), 3)  # asistencias
        self.assertEqual(sum(f[3] for f in meses), 1)  # presentes

    def test_demografia_reparte_por_rango_de_edad(self):
        reporte = consultas.demografia()
        edades = {f[0]: f[1] for f in reporte.secciones[2].filas}
        self.assertEqual(edades["Menores de 18"], 1)  # Luis, 16
        self.assertEqual(edades["26 a 35 años"], 1)  # Ana, 34
        self.assertEqual(edades["46 a 60 años"], 1)  # Carlos, 48
        self.assertEqual(edades["18 a 25 años"], 0)
        self.assertEqual(edades["Sin fecha de nacimiento"], 1)  # Marta

    def test_demografia_resumen_cuenta_activos_y_ministerios(self):
        resumen = dict(consultas.demografia().resumen)
        self.assertEqual(resumen["Miembros registrados"], 4)
        self.assertEqual(resumen["Miembros activos"], 2)  # Ana y Carlos
        self.assertEqual(resumen["Miembros con familia asignada"], 2)
        self.assertEqual(resumen["Miembros en algún ministerio"], 2)

    def test_porcentaje_evita_la_division_por_cero(self):
        self.assertEqual(consultas._pct(0, 0), 0.0)
        self.assertEqual(consultas._pct(0, 4), 0.0)
        self.assertEqual(consultas._pct(1, 4), 25.0)
        self.assertEqual(consultas._pct(2, 3), 66.7)

    def test_filtro_de_fechas_recorta_los_dos_eventos(self):
        desde = self.hoy - timedelta(days=4)
        reporte = consultas.asistencia_por_evento(desde=desde)
        nombres = [f[0] for f in reporte.secciones[0].filas]
        self.assertEqual(nombres, ["Ensayo de alabanza"])

    def test_filtros_se_documentan_en_el_reporte(self):
        desde = date(2026, 1, 1)
        hasta = date(2026, 12, 31)
        reporte = consultas.asistencia_por_evento(desde=desde, hasta=hasta, tipo="culto")
        self.assertEqual(
            reporte.filtros,
            {"Desde": "01/01/2026", "Hasta": "31/12/2026", "Tipo de evento": "culto"},
        )


class EdadesDelReporte(BaseSistema):
    """Limites de los rangos: el cumpleanos de hoy ya cuenta."""

    def _crear(self, anios, **kwargs):
        cumple = kwargs.pop("cumple", (1, 15))
        return Miembro.objects.create(
            nombres="Prueba",
            apellidos=f"Edad {anios}",
            estado="activo",
            fecha_nacimiento=date(self.hoy.year - anios, *cumple),
        )

    def test_rangos_sin_huecos_ni_solapes(self):
        self.assertEqual(RANGOS_EDAD[0][1], 0)
        for (_, _, maximo), (_, minimo, _) in zip(RANGOS_EDAD, RANGOS_EDAD[1:]):
            self.assertEqual(minimo, maximo + 1)
        self.assertGreaterEqual(RANGOS_EDAD[-1][2], 120)

    def test_cumple_hoy_entra_en_el_rango_de_18(self):
        self._crear(18, cumple=(self.hoy.month, self.hoy.day))
        edades = {f[0]: f[1] for f in consultas.demografia().secciones[2].filas}
        self.assertEqual(edades["18 a 25 años"], 1)

    def test_cumple_manana_todavia_tiene_17(self):
        manana = self.hoy + timedelta(days=1)
        self._crear(18, cumple=(manana.month, manana.day))
        edades = {f[0]: f[1] for f in consultas.demografia().secciones[2].filas}
        self.assertEqual(edades["Menores de 18"], 2)  # Luis + el nuevo

    def test_limite_inferior_y_superior_de_cada_rango(self):
        # 17, 18, 25, 26, 60, 61: cada uno debe caer en un unico rango, sin
        # mover ninguno de los demas conteos.
        esperado = {
            17: "Menores de 18",
            18: "18 a 25 años",
            25: "18 a 25 años",
            26: "26 a 35 años",
            60: "46 a 60 años",
            61: "Mayores de 60",
        }
        for anios, rango in esperado.items():
            with self.subTest(anios=anios):
                Miembro.objects.filter(apellidos__startswith="Edad ").delete()
                antes = {
                    f[0]: f[1] for f in consultas.demografia().secciones[2].filas
                }
                self._crear(anios, cumple=(self.hoy.month, self.hoy.day))
                despues = {
                    f[0]: f[1] for f in consultas.demografia().secciones[2].filas
                }
                for etiqueta, n in antes.items():
                    if etiqueta == rango:
                        self.assertEqual(despues[etiqueta], n + 1, etiqueta)
                    else:
                        self.assertEqual(despues[etiqueta], n, etiqueta)


class ApoyoDeReportes(BaseSistema):
    def test_a_fecha_acepta_solo_iso(self):
        self.assertEqual(consultas.a_fecha("2026-11-20"), date(2026, 11, 20))
        self.assertEqual(consultas.a_fecha("  2026-11-20  "), date(2026, 11, 20))
        self.assertIsNone(consultas.a_fecha("20/11/2026"))
        self.assertIsNone(consultas.a_fecha("2026-13-01"))
        self.assertIsNone(consultas.a_fecha(""))
        self.assertIsNone(consultas.a_fecha(None))

    def test_reporte_vacio_solo_si_ninguna_seccion_tiene_filas(self):
        vacio = Reporte(clave="x", titulo="X", descripcion="")
        self.assertTrue(vacio.vacio)
        vacio.secciones.append(Seccion("S", ["A"], []))
        self.assertTrue(vacio.vacio)
        vacio.secciones[0].filas.append(["dato"])
        self.assertFalse(vacio.vacio)

    def test_nombre_de_archivo_lleva_clave_y_fecha(self):
        hoy = date.today()
        self.assertEqual(
            nombre_archivo("asistencia", "pdf"),
            f"reporte_asistencia_{hoy:%Y%m%d}.pdf",
        )
        self.assertEqual(
            nombre_archivo("demografia", "xlsx"),
            f"reporte_demografia_{hoy:%Y%m%d}.xlsx",
        )

    def test_catalogo_tiene_los_cuatro_reportes_con_titulo(self):
        self.assertEqual(
            set(consultas.CATALOGO),
            {"asistencia", "crecimiento", "inventario", "demografia"},
        )
        for clave, (titulo, funcion) in consultas.CATALOGO.items():
            with self.subTest(clave=clave):
                self.assertTrue(titulo)
                self.assertEqual(funcion().clave, clave)


class FechasDeReferencia(BaseSistema):
    """timezone.localdate() es la unica fuente de 'hoy' en las reglas."""

    def test_el_escenario_usa_fechas_relativas(self):
        self.assertLess(self.culto.fecha, self.hoy)
        self.assertGreater(self.prestamo.fecha_devolucion_prevista, self.hoy)
        self.assertEqual(timezone.localdate(), self.hoy)

    def test_las_edades_del_escenario_no_cambian_con_el_tiempo(self):
        self.assertEqual(consultas.demografia().clave, "demografia")
        # nacido() se calcula desde hoy; el rango esperado no depende del anio.
        self.assertLess(nacido(34), self.hoy)
