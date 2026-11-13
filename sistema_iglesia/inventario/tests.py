"""Pruebas del modulo de inventario (Semana 6, viernes).

Cubren registro, listado, busqueda, detalle, edicion y el flujo de
prestamos/devoluciones con control de existencias disponibles.
Se ejecutan sobre SQLite en memoria (ver config/settings.py, bloque de test).
"""

from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from miembros.models import Miembro

from .forms import EquipoForm, PrestamoForm
from .models import Equipo, Prestamo


class InventarioCrudTests(TestCase):
    def setUp(self):
        self.miembro = Miembro.objects.create(nombres="Hector", apellidos="Hernandez")
        self.equipo = Equipo.objects.create(
            nombre="Guitarra acustica", categoria="instrumento", cantidad=3, estado="disponible"
        )

    # --- Registro / listado ---
    def test_listado_muestra_equipos(self):
        r = self.client.get(reverse("inventario:lista"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Guitarra acustica")

    def test_registro_guarda_en_bd(self):
        r = self.client.post(
            reverse("inventario:registrar"),
            {"nombre": "Microfono Shure", "categoria": "sonido", "cantidad": 2, "estado": "disponible"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Equipo.objects.filter(nombre="Microfono Shure").exists())

    def test_registro_rechaza_nombre_vacio(self):
        r = self.client.post(
            reverse("inventario:registrar"), {"nombre": "", "categoria": "sonido", "cantidad": 1}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Equipo.objects.count(), 1)

    def test_formulario_rechaza_cantidad_cero(self):
        form = EquipoForm(data={"nombre": "X", "categoria": "recurso", "cantidad": 0})
        self.assertFalse(form.is_valid())
        self.assertIn("cantidad", form.errors)

    # --- Busqueda ---
    def test_busqueda_por_nombre(self):
        r = self.client.get(reverse("inventario:lista"), {"q": "guitarra"})
        self.assertContains(r, "Guitarra acustica")

    def test_busqueda_por_categoria(self):
        r = self.client.get(reverse("inventario:lista"), {"q": "instrumento"})
        self.assertContains(r, "Guitarra acustica")

    def test_busqueda_sin_resultados(self):
        r = self.client.get(reverse("inventario:lista"), {"q": "zzzz"})
        self.assertNotContains(r, "Guitarra acustica")

    # --- Detalle / edicion ---
    def test_detalle_muestra_equipo(self):
        r = self.client.get(reverse("inventario:detalle", args=[self.equipo.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Guitarra acustica")

    def test_detalle_inexistente_da_404(self):
        r = self.client.get(reverse("inventario:detalle", args=[99999]))
        self.assertEqual(r.status_code, 404)

    def test_edicion_actualiza_ubicacion_y_cantidad(self):
        r = self.client.post(
            reverse("inventario:editar", args=[self.equipo.pk]),
            {"nombre": "Guitarra acustica", "categoria": "instrumento",
             "cantidad": 5, "estado": "disponible", "ubicacion": "Bodega B"},
        )
        self.assertEqual(r.status_code, 302)
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.cantidad, 5)
        self.assertEqual(self.equipo.ubicacion, "Bodega B")

    # --- Prestamos ---
    def test_prestamo_guarda_y_reduce_disponible(self):
        r = self.client.post(
            reverse("inventario:prestamos"),
            {"equipo": self.equipo.pk, "miembro": self.miembro.pk, "cantidad": 2,
             "fecha_prestamo": date.today(), "fecha_devolucion_prevista": date.today() + timedelta(days=7)},
        )
        self.assertEqual(r.status_code, 302)
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.cantidad_disponible, 1)

    def test_prestamo_no_supera_existencias(self):
        form = PrestamoForm(
            data={"equipo": self.equipo.pk, "miembro": self.miembro.pk, "cantidad": 99,
                  "fecha_prestamo": date.today(), "fecha_devolucion_prevista": date.today() + timedelta(days=7)}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("cantidad", form.errors)
        self.assertEqual(Prestamo.objects.count(), 0)

    def test_prestamo_rechaza_fecha_devolucion_anterior(self):
        form = PrestamoForm(
            data={"equipo": self.equipo.pk, "miembro": self.miembro.pk, "cantidad": 1,
                  "fecha_prestamo": date.today(), "fecha_devolucion_prevista": date.today() - timedelta(days=1)}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_devolucion_prevista", form.errors)

    # --- Devoluciones ---
    def test_devolucion_libera_stock(self):
        prestamo = Prestamo.objects.create(
            equipo=self.equipo, miembro=self.miembro, cantidad=2,
            fecha_prestamo=date.today(), fecha_devolucion_prevista=date.today() + timedelta(days=7),
        )
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.cantidad_disponible, 1)
        r = self.client.post(reverse("inventario:devoluciones"), {"prestamo_id": prestamo.pk})
        self.assertEqual(r.status_code, 302)
        prestamo.refresh_from_db()
        self.equipo.refresh_from_db()
        self.assertEqual(prestamo.estado, "devuelto")
        self.assertIsNotNone(prestamo.fecha_devolucion_real)
        self.assertEqual(self.equipo.cantidad_disponible, 3)

    def test_devoluciones_lista_solo_activos(self):
        Prestamo.objects.create(
            equipo=self.equipo, miembro=self.miembro, cantidad=1,
            fecha_prestamo=date.today(), fecha_devolucion_prevista=date.today() + timedelta(days=7),
        )
        Prestamo.objects.create(
            equipo=self.equipo, miembro=self.miembro, cantidad=1, estado="devuelto",
            fecha_prestamo=date.today(), fecha_devolucion_prevista=date.today(),
            fecha_devolucion_real=date.today(),
        )
        r = self.client.get(reverse("inventario:devoluciones"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context["prestamos"]), 1)


class PrestamoMiembroInactivoTests(TestCase):
    """Semana 10: un miembro inactivo no puede ser responsable de un prestamo nuevo."""

    def setUp(self):
        self.activo = Miembro.objects.create(nombres="Ana", apellidos="Activa")
        self.inactivo = Miembro.objects.create(
            nombres="Beto", apellidos="Inactivo", estado="inactivo"
        )
        self.equipo = Equipo.objects.create(
            nombre="Parlante", categoria="sonido", cantidad=2, estado="disponible"
        )

    def _datos(self, miembro):
        return {
            "equipo": self.equipo.pk,
            "miembro": miembro.pk,
            "cantidad": 1,
            "fecha_prestamo": date.today(),
            "fecha_devolucion_prevista": date.today() + timedelta(days=3),
        }

    def test_alta_rechaza_miembro_inactivo(self):
        form = PrestamoForm(data=self._datos(self.inactivo))
        self.assertFalse(form.is_valid())
        self.assertIn("miembro", form.errors)
        self.assertEqual(Prestamo.objects.count(), 0)

    def test_alta_acepta_miembro_activo(self):
        form = PrestamoForm(data=self._datos(self.activo))
        self.assertTrue(form.is_valid(), form.errors)

    def test_queryset_de_miembros_excluye_inactivos(self):
        form = PrestamoForm()
        ids = set(form.fields["miembro"].queryset.values_list("pk", flat=True))
        self.assertIn(self.activo.pk, ids)
        self.assertNotIn(self.inactivo.pk, ids)

    def test_edicion_conserva_miembro_inactivo(self):
        prestamo = Prestamo.objects.create(
            equipo=self.equipo,
            miembro=self.inactivo,
            cantidad=1,
            fecha_prestamo=date.today(),
            fecha_devolucion_prevista=date.today() + timedelta(days=3),
        )
        form = PrestamoForm(data=self._datos(self.inactivo), instance=prestamo)
        self.assertTrue(form.is_valid(), form.errors)
        ids = set(form.fields["miembro"].queryset.values_list("pk", flat=True))
        self.assertIn(self.inactivo.pk, ids)
