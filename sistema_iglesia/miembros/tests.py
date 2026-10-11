"""Pruebas del modulo de miembros (Semana 5, viernes).

Cubren registro, listado, detalle, edicion, baja logica,
validaciones y el manejo de registros inexistentes.
"""

from django.test import TestCase
from django.urls import reverse

from .forms import MiembroForm
from .models import Miembro


class MiembroCrudTests(TestCase):
    def setUp(self):
        self.miembro = Miembro.objects.create(
            nombres="Juan", apellidos="Pérez", telefono="0000-0000", estado="activo"
        )

    def test_listado_muestra_registros(self):
        r = self.client.get(reverse("miembros:lista"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Juan")

    def test_registro_guarda_en_bd(self):
        r = self.client.post(
            reverse("miembros:registrar"),
            {"nombres": "María", "apellidos": "López", "estado": "activo"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(
            Miembro.objects.filter(nombres="María", apellidos="López").exists()
        )

    def test_registro_rechaza_datos_incompletos(self):
        r = self.client.post(
            reverse("miembros:registrar"), {"nombres": "", "apellidos": ""}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Miembro.objects.count(), 1)

    def test_registro_rechaza_email_invalido(self):
        form = MiembroForm(
            data={"nombres": "A", "apellidos": "B", "email": "no-es-correo"}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_detalle_muestra_miembro(self):
        r = self.client.get(reverse("miembros:detalle", args=[self.miembro.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Juan")

    def test_detalle_inexistente_da_404(self):
        r = self.client.get(reverse("miembros:detalle", args=[99999]))
        self.assertEqual(r.status_code, 404)

    def test_edicion_actualiza_datos(self):
        r = self.client.post(
            reverse("miembros:editar", args=[self.miembro.pk]),
            {"nombres": "Juan", "apellidos": "Pérez", "telefono": "0111-2222",
             "estado": "activo"},
        )
        self.assertEqual(r.status_code, 302)
        self.miembro.refresh_from_db()
        self.assertEqual(self.miembro.telefono, "0111-2222")

    def test_eliminacion_es_baja_logica(self):
        r = self.client.post(reverse("miembros:eliminar", args=[self.miembro.pk]))
        self.assertEqual(r.status_code, 302)
        self.miembro.refresh_from_db()
        self.assertEqual(self.miembro.estado, "inactivo")
        # El registro se conserva en la base de datos.
        self.assertTrue(Miembro.objects.filter(pk=self.miembro.pk).exists())

    def test_confirmacion_previa_a_la_baja(self):
        r = self.client.get(reverse("miembros:eliminar", args=[self.miembro.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Confirmar baja")
