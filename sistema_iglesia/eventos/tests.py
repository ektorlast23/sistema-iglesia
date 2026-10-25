"""Pruebas del modulo de eventos y asistencia (Semana 7, viernes).

Cubren modelos, formularios y vistas del CRUD de eventos, el registro de
asistencia por evento y la consulta del historial por miembro.
Se ejecutan sobre SQLite en memoria (ver config/settings.py, bloque de test).
"""

from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from miembros.models import Miembro

from .forms import AsistenciaForm, EventoForm
from .models import Asistencia, Evento


class ModeloTests(TestCase):
    def setUp(self):
        self.miembro = Miembro.objects.create(nombres="Hector", apellidos="Hernandez")
        self.evento = Evento.objects.create(
            nombre="Culto Dominical",
            fecha=date(2026, 10, 25),
            hora_inicio=time(9, 0),
            hora_fin=time(11, 0),
            lugar="Templo principal",
            tipo="culto",
        )

    # --- Evento ---
    def test_evento_se_crea(self):
        self.assertEqual(Evento.objects.count(), 1)
        self.assertEqual(self.evento.nombre, "Culto Dominical")

    def test_evento_str_devuelve_nombre_y_fecha(self):
        self.assertEqual(str(self.evento), "Culto Dominical (2026-10-25)")

    # --- Asistencia ---
    def test_asistencia_estado_por_defecto_presente(self):
        asistencia = Asistencia.objects.create(
            miembro=self.miembro, evento=self.evento, fecha=self.evento.fecha
        )
        self.assertEqual(asistencia.estado, "presente")
        self.assertEqual(asistencia.get_estado_display(), "Presente")

    def test_asistencia_estado_ausente(self):
        asistencia = Asistencia.objects.create(
            miembro=self.miembro, evento=self.evento, fecha=self.evento.fecha, estado="ausente"
        )
        self.assertEqual(asistencia.estado, "ausente")

    def test_asistencia_estado_justificado(self):
        asistencia = Asistencia.objects.create(
            miembro=self.miembro, evento=self.evento, fecha=self.evento.fecha, estado="justificado"
        )
        self.assertEqual(asistencia.estado, "justificado")

    def test_asistencia_estado_retraso(self):
        asistencia = Asistencia.objects.create(
            miembro=self.miembro, evento=self.evento, fecha=self.evento.fecha, estado="retraso"
        )
        self.assertEqual(asistencia.estado, "retraso")

    def test_asistencia_str(self):
        asistencia = Asistencia.objects.create(
            miembro=self.miembro, evento=self.evento, fecha=self.evento.fecha
        )
        self.assertEqual(
            str(asistencia),
            "Hector Hernandez en Culto Dominical (2026-10-25): Presente",
        )


class FormularioTests(TestCase):
    def setUp(self):
        self.miembro = Miembro.objects.create(nombres="Hector", apellidos="Hernandez")
        self.evento = Evento.objects.create(
            nombre="Culto Dominical", fecha=date(2026, 10, 25)
        )

    # --- EventoForm ---
    def test_evento_form_valido(self):
        form = EventoForm(
            data={
                "nombre": "Vigilia de oracion",
                "descripcion": "Vigilia mensual",
                "fecha": "2026-11-06",
                "hora_inicio": "19:00",
                "hora_fin": "22:00",
                "lugar": "Templo principal",
                "tipo": "vigilia",
                "responsable": self.miembro.pk,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_evento_form_invalido_sin_nombre(self):
        form = EventoForm(
            data={"nombre": "", "fecha": "2026-11-06", "hora_inicio": "19:00"}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_evento_form_rechaza_hora_fin_menor_que_inicio(self):
        form = EventoForm(
            data={
                "nombre": "Ensayo",
                "fecha": "2026-11-06",
                "hora_inicio": "19:00",
                "hora_fin": "18:00",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("hora_fin", form.errors)

    # --- AsistenciaForm ---
    def test_asistencia_form_valido(self):
        form = AsistenciaForm(
            data={
                "miembro": self.miembro.pk,
                "evento": self.evento.pk,
                "fecha": "2026-10-25",
                "estado": "presente",
                "observaciones": "",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_asistencia_form_rechaza_duplicado(self):
        Asistencia.objects.create(
            miembro=self.miembro, evento=self.evento, fecha=self.evento.fecha
        )
        form = AsistenciaForm(
            data={
                "miembro": self.miembro.pk,
                "evento": self.evento.pk,
                "fecha": "2026-10-25",
                "estado": "presente",
                "observaciones": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)


class VistaTests(TestCase):
    def setUp(self):
        self.miembro = Miembro.objects.create(nombres="Hector", apellidos="Hernandez")
        self.otro_miembro = Miembro.objects.create(nombres="Melissa", apellidos="Hernandez")
        self.evento = Evento.objects.create(
            nombre="Culto Dominical",
            fecha=date(2026, 10, 25),
            hora_inicio=time(9, 0),
            hora_fin=time(11, 0),
            lugar="Templo principal",
            tipo="culto",
            responsable=self.miembro,
        )
        self.asistencia = Asistencia.objects.create(
            miembro=self.miembro, evento=self.evento, fecha=self.evento.fecha
        )

    # --- CRUD de eventos ---
    def test_lista_eventos(self):
        r = self.client.get(reverse("eventos:lista"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Culto Dominical")

    def test_formulario_nuevo_evento(self):
        r = self.client.get(reverse("eventos:registrar"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Registrar evento")

    def test_registrar_evento_guarda_en_bd(self):
        r = self.client.post(
            reverse("eventos:registrar"),
            {
                "nombre": "Vigilia de oracion",
                "descripcion": "",
                "fecha": "2026-11-06",
                "hora_inicio": "19:00",
                "hora_fin": "22:00",
                "lugar": "Templo principal",
                "tipo": "vigilia",
                "responsable": self.miembro.pk,
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Evento.objects.filter(nombre="Vigilia de oracion").exists())

    def test_detalle_evento(self):
        r = self.client.get(reverse("eventos:detalle", args=[self.evento.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Culto Dominical")

    def test_detalle_inexistente_da_404(self):
        r = self.client.get(reverse("eventos:detalle", args=[99999]))
        self.assertEqual(r.status_code, 404)

    def test_formulario_editar_evento(self):
        r = self.client.get(reverse("eventos:editar", args=[self.evento.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Culto Dominical")

    def test_editar_evento_actualiza_datos(self):
        r = self.client.post(
            reverse("eventos:editar", args=[self.evento.pk]),
            {
                "nombre": "Culto Dominical",
                "descripcion": "",
                "fecha": "2026-10-25",
                "hora_inicio": "10:00",
                "hora_fin": "12:00",
                "lugar": "Salon principal",
                "tipo": "culto",
                "responsable": self.miembro.pk,
            },
        )
        self.assertEqual(r.status_code, 302)
        self.evento.refresh_from_db()
        self.assertEqual(self.evento.lugar, "Salon principal")
        self.assertEqual(self.evento.hora_inicio, time(10, 0))

    def test_eliminar_evento_desde_formulario(self):
        r = self.client.get(reverse("eventos:eliminar", args=[self.evento.pk]))
        self.assertEqual(r.status_code, 200)

    def test_eliminar_evento_lo_borra(self):
        r = self.client.post(reverse("eventos:eliminar", args=[self.evento.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Evento.objects.filter(pk=self.evento.pk).exists())

    # --- Asistencia ---
    def test_formulario_asistencia(self):
        r = self.client.get(
            reverse("eventos:asistencia_registrar", args=[self.evento.pk])
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Registrar asistencia")

    def test_registrar_asistencia_guarda_en_bd(self):
        r = self.client.post(
            reverse("eventos:asistencia_registrar", args=[self.evento.pk]),
            {
                "miembro": self.otro_miembro.pk,
                "evento": self.evento.pk,
                "fecha": "2026-10-25",
                "estado": "presente",
                "observaciones": "",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(
            Asistencia.objects.filter(
                miembro=self.otro_miembro, evento=self.evento
            ).exists()
        )
        self.assertEqual(Asistencia.objects.count(), 2)

    def test_asistencia_duplicada_no_se_guarda(self):
        r = self.client.post(
            reverse("eventos:asistencia_registrar", args=[self.evento.pk]),
            {
                "miembro": self.miembro.pk,
                "evento": self.evento.pk,
                "fecha": "2026-10-25",
                "estado": "presente",
                "observaciones": "",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Asistencia.objects.count(), 1)

    def test_lista_asistencias_muestra_total(self):
        r = self.client.get(
            reverse("eventos:lista_asistencias", args=[self.evento.pk])
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["total_asistentes"], 1)
        self.assertContains(r, "Total de asistentes")

    def test_consulta_asistencias_por_miembro(self):
        r = self.client.get(reverse("eventos:asistencia_consulta_miembro"))
        self.assertEqual(r.status_code, 200)

    def test_consulta_asistencias_filtra_miembro(self):
        r = self.client.get(
            reverse("eventos:asistencia_consulta_miembro"),
            {"miembro_id": self.miembro.pk},
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Culto Dominical")
        self.assertEqual(len(r.context["asistencias"]), 1)

    def test_consulta_miembro_inexistente_da_404(self):
        r = self.client.get(
            reverse("eventos:asistencia_consulta_miembro"), {"miembro_id": 99999}
        )
        self.assertEqual(r.status_code, 404)
