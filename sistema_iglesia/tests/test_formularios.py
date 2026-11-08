"""Validacion de formularios, campo por campo (Semana 9).

Cada formulario del sistema se prueba con datos validos y con datos que deben
rechazarse. La idea es que la validacion quede documentada como una matriz: que
campo se exige, que rango se controla y que mensaje ve el usuario.
"""

from datetime import timedelta

from django.test import TestCase

from eventos.forms import AsistenciaEditarForm, AsistenciaForm, EventoForm
from eventos.models import Asistencia, Evento
from inventario.forms import EquipoForm, PrestamoForm
from inventario.models import Equipo
from miembros.forms import MiembroForm

from .base import BaseSistema


class FormularioMiembro(BaseSistema):
    def test_datos_minimos_validos(self):
        form = MiembroForm(
            data={"nombres": "Rosa", "apellidos": "Mejia", "estado": "activo"}
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_nombres_y_apellidos_son_obligatorios(self):
        form = MiembroForm(data={"estado": "activo"})
        self.assertFalse(form.is_valid())
        self.assertIn("nombres", form.errors)
        self.assertIn("apellidos", form.errors)

    def test_estado_es_obligatorio_en_el_post(self):
        # El modelo tiene default 'activo', pero el formulario lo exige: si el
        # navegador no envia el select, se rechaza en vez de asumir un valor.
        form = MiembroForm(data={"nombres": "Rosa", "apellidos": "Mejia"})
        self.assertFalse(form.is_valid())
        self.assertIn("estado", form.errors)

    def test_estado_fuera_de_lista_se_rechaza(self):
        form = MiembroForm(
            data={"nombres": "Rosa", "apellidos": "Mejia", "estado": "jubilado"}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("estado", form.errors)

    def test_email_invalido_se_rechaza(self):
        form = MiembroForm(
            data={
                "nombres": "Rosa",
                "apellidos": "Mejia",
                "estado": "activo",
                "email": "rosa-arroba-iglesia",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_email_vacio_es_valido(self):
        form = MiembroForm(
            data={"nombres": "Rosa", "apellidos": "Mejia", "estado": "activo", "email": ""}
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_telefono_de_mas_de_20_caracteres_se_rechaza(self):
        form = MiembroForm(
            data={
                "nombres": "Rosa",
                "apellidos": "Mejia",
                "estado": "activo",
                "telefono": "7" * 21,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("telefono", form.errors)
        self.assertIn("20 caracteres", str(form.errors["telefono"]))

    def test_telefono_se_guarda_sin_espacios(self):
        form = MiembroForm(
            data={
                "nombres": "Rosa",
                "apellidos": "Mejia",
                "estado": "activo",
                "telefono": "  7000-0001  ",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["telefono"], "7000-0001")

    def test_fecha_de_nacimiento_invalida_se_rechaza(self):
        form = MiembroForm(
            data={
                "nombres": "Rosa",
                "apellidos": "Mejia",
                "estado": "activo",
                "fecha_nacimiento": "1995-13-45",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_nacimiento", form.errors)

    def test_familia_inexistente_se_rechaza(self):
        form = MiembroForm(
            data={
                "nombres": "Rosa",
                "apellidos": "Mejia",
                "estado": "activo",
                "familia": 99999,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("familia", form.errors)

    def test_los_campos_de_fecha_usan_selector_de_fecha(self):
        form = MiembroForm()
        for campo in ("fecha_nacimiento", "fecha_ingreso"):
            with self.subTest(campo=campo):
                self.assertEqual(form.fields[campo].widget.input_type, "date")


class FormularioEvento(BaseSistema):
    def datos(self, **cambios):
        datos = {
            "nombre": "Vigilia",
            "fecha": "2026-11-20",
            "hora_inicio": "19:00",
            "hora_fin": "21:00",
        }
        datos.update(cambios)
        return datos

    def test_evento_valido(self):
        form = EventoForm(data=self.datos())
        self.assertTrue(form.is_valid(), form.errors)

    def test_hora_fin_anterior_a_inicio_se_rechaza(self):
        form = EventoForm(
            data=self.datos(hora_inicio="21:00", hora_fin="19:00")
        )
        self.assertFalse(form.is_valid())
        self.assertIn("hora_fin", form.errors)
        self.assertIn("anterior", str(form.errors["hora_fin"]))

    def test_horas_iguales_son_validas(self):
        form = EventoForm(data=self.datos(hora_inicio="10:00", hora_fin="10:00"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_horas_opcionales(self):
        form = EventoForm(data=self.datos(hora_inicio="", hora_fin=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_nombre_es_obligatorio(self):
        form = EventoForm(data=self.datos(nombre=""))
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_responsable_inactivo_se_rechaza(self):
        form = EventoForm(data=self.datos(responsable=self.marta.pk))
        self.assertFalse(form.is_valid())
        self.assertIn("responsable", form.errors)

    def test_solo_miembros_activos_como_responsable(self):
        queryset = EventoForm().fields["responsable"].queryset
        self.assertIn(self.ana, queryset)
        self.assertNotIn(self.marta, queryset)  # inactivo
        self.assertNotIn(self.luis, queryset)  # visitante

    def test_fecha_iso_y_formato_local_son_validas(self):
        # Con LANGUAGE_CODE='es' Django acepta AAAA-MM-DD y DD/MM/AAAA: el
        # usuario puede escribir la fecha como esta acostumbrado.
        for valor in ("2026-11-20", "20/11/2026"):
            with self.subTest(valor=valor):
                form = EventoForm(data=self.datos(fecha=valor))
                self.assertTrue(form.is_valid(), form.errors)

    def test_fecha_imposible_se_rechaza(self):
        form = EventoForm(data=self.datos(fecha="31/02/2026"))
        self.assertFalse(form.is_valid())
        self.assertIn("fecha", form.errors)

    def test_las_horas_usan_selector_de_hora(self):
        form = EventoForm()
        for campo in ("hora_inicio", "hora_fin"):
            with self.subTest(campo=campo):
                self.assertEqual(form.fields[campo].widget.input_type, "time")


class FormularioAsistencia(BaseSistema):
    def setUp(self):
        super().setUp()
        self.nuevo_evento = Evento.objects.create(
            nombre="Reunion de jovenes", fecha=self.hoy, tipo="reunion"
        )

    def datos(self, **cambios):
        datos = {
            "miembro": self.ana.pk,
            "evento": self.nuevo_evento.pk,
            "fecha": self.hoy.isoformat(),
            "estado": "presente",
            "observaciones": "",
        }
        datos.update(cambios)
        return datos

    def test_asistencia_valida(self):
        form = AsistenciaForm(data=self.datos())
        self.assertTrue(form.is_valid(), form.errors)

    def test_duplicado_en_el_mismo_evento_se_rechaza(self):
        form = AsistenciaForm(
            data=self.datos(miembro=self.ana.pk, evento=self.culto.pk)
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn("ya tiene asistencia", str(form.errors["__all__"]))

    def test_editar_la_misma_asistencia_no_es_duplicado(self):
        existente = Asistencia.objects.get(miembro=self.ana, evento=self.culto)
        form = AsistenciaForm(data=self.datos(miembro=self.ana.pk, evento=self.culto.pk),
                              instance=existente)
        self.assertTrue(form.is_valid(), form.errors)

    def test_miembro_inactivo_se_rechaza(self):
        form = AsistenciaForm(data=self.datos(miembro=self.marta.pk))
        self.assertFalse(form.is_valid())
        self.assertIn("miembro", form.errors)

    def test_estado_fuera_de_lista_se_rechaza(self):
        form = AsistenciaForm(data=self.datos(estado="tal vez"))
        self.assertFalse(form.is_valid())
        self.assertIn("estado", form.errors)

    def test_observaciones_de_mas_de_255_se_rechazan(self):
        form = AsistenciaForm(data=self.datos(observaciones="x" * 256))
        self.assertFalse(form.is_valid())
        self.assertIn("observaciones", form.errors)

    def test_fecha_es_obligatoria(self):
        form = AsistenciaForm(data=self.datos(fecha=""))
        self.assertFalse(form.is_valid())
        self.assertIn("fecha", form.errors)

    def test_el_formulario_de_edicion_solo_cambia_estado_y_observaciones(self):
        form = AsistenciaEditarForm()
        self.assertEqual(list(form.fields), ["estado", "observaciones"])


class FormularioEquipo(BaseSistema):
    def datos(self, **cambios):
        datos = {
            "nombre": "Micrófono",
            "categoria": "sonido",
            "descripcion": "",
            "cantidad": 2,
            "estado": "disponible",
            "ubicacion": "Bodega",
        }
        datos.update(cambios)
        return datos

    def test_equipo_valido(self):
        form = EquipoForm(data=self.datos())
        self.assertTrue(form.is_valid(), form.errors)

    def test_cantidad_cero_se_rechaza(self):
        form = EquipoForm(data=self.datos(cantidad=0))
        self.assertFalse(form.is_valid())
        self.assertIn("cantidad", form.errors)
        self.assertIn("al menos 1", str(form.errors["cantidad"]))

    def test_cantidad_negativa_se_rechaza(self):
        form = EquipoForm(data=self.datos(cantidad=-3))
        self.assertFalse(form.is_valid())
        self.assertIn("cantidad", form.errors)

    def test_cantidad_no_numerica_se_rechaza(self):
        form = EquipoForm(data=self.datos(cantidad="dos"))
        self.assertFalse(form.is_valid())
        self.assertIn("cantidad", form.errors)

    def test_categoria_fuera_de_lista_se_rechaza(self):
        form = EquipoForm(data=self.datos(categoria="cocina"))
        self.assertFalse(form.is_valid())
        self.assertIn("categoria", form.errors)

    def test_estado_fuera_de_lista_se_rechaza(self):
        form = EquipoForm(data=self.datos(estado="perdido"))
        self.assertFalse(form.is_valid())
        self.assertIn("estado", form.errors)


class FormularioPrestamo(BaseSistema):
    def datos(self, **cambios):
        datos = {
            "equipo": self.guitarra.pk,
            "miembro": self.carlos.pk,
            "cantidad": 1,
            "fecha_prestamo": self.hoy.isoformat(),
            "fecha_devolucion_prevista": (self.hoy + timedelta(days=7)).isoformat(),
            "observaciones": "",
        }
        datos.update(cambios)
        return datos

    def test_prestamo_valido(self):
        form = PrestamoForm(data=self.datos())
        self.assertTrue(form.is_valid(), form.errors)

    def test_no_puede_exceder_lo_disponible(self):
        # 3 unidades, 1 ya prestada => 2 disponibles.
        form = PrestamoForm(data=self.datos(cantidad=3))
        self.assertFalse(form.is_valid())
        self.assertIn("Solo hay 2 unidad", str(form.errors["cantidad"]))

    def test_puede_prestar_exactamente_lo_disponible(self):
        form = PrestamoForm(data=self.datos(cantidad=2))
        self.assertTrue(form.is_valid(), form.errors)

    def test_cantidad_cero_se_rechaza(self):
        form = PrestamoForm(data=self.datos(cantidad=0))
        self.assertFalse(form.is_valid())
        self.assertIn("cantidad", form.errors)

    def test_devolucion_anterior_al_prestamo_se_rechaza(self):
        form = PrestamoForm(
            data=self.datos(
                fecha_prestamo=self.hoy.isoformat(),
                fecha_devolucion_prevista=(self.hoy - timedelta(days=1)).isoformat(),
            )
        )
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_devolucion_prevista", form.errors)

    def test_equipo_de_baja_se_rechaza(self):
        form = PrestamoForm(data=self.datos(equipo=self.proyector.pk))
        self.assertFalse(form.is_valid())
        self.assertIn("equipo", form.errors)

    def test_miembro_es_obligatorio(self):
        form = PrestamoForm(data=self.datos(miembro=""))
        self.assertFalse(form.is_valid())
        self.assertIn("miembro", form.errors)

    def test_fechas_son_obligatorias(self):
        form = PrestamoForm(
            data=self.datos(fecha_prestamo="", fecha_devolucion_prevista="")
        )
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_prestamo", form.errors)
        self.assertIn("fecha_devolucion_prevista", form.errors)
