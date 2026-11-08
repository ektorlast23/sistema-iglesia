"""Datos de partida compartidos por las pruebas de la Semana 9.

Un juego de datos pequeño y explicito: cuatro miembros (uno inactivo, uno
visitante), dos ministerios, dos eventos con asistencias y tres equipos con un
prestamo activo. Cada prueba parte de aqui, asi que las cifras esperadas se
leen a simple vista.
"""

from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from eventos.models import Asistencia, Evento
from inventario.models import Equipo, Prestamo
from miembros.models import Familia, Miembro, MiembroMinisterio, Ministerio


def nacido(hace_anios: int) -> date:
    """Fecha de nacimiento estable: 15 de enero de hace N anios.

    Se calcula desde hoy para que los rangos de edad del reporte demografico no
    cambien con el paso del tiempo.
    """
    return date(timezone.localdate().year - hace_anios, 1, 15)


class BaseSistema(TestCase):
    """Escenario base: 4 miembros, 2 eventos, 3 equipos y 1 prestamo."""

    @classmethod
    def setUpTestData(cls):
        cls.hoy = timezone.localdate()

    def setUp(self):
        self.familia = Familia.objects.create(
            nombre_familia="Hernandez", telefono="2222-0000"
        )
        self.alabanza = Ministerio.objects.create(nombre="Alabanza")
        self.jovenes = Ministerio.objects.create(nombre="Jovenes")

        self.ana = Miembro.objects.create(
            nombres="Ana",
            apellidos="Hernandez",
            sexo="F",
            fecha_nacimiento=nacido(34),
            estado="activo",
            familia=self.familia,
            email="ana@iglesia.test",
            telefono="7000-0001",
        )
        self.carlos = Miembro.objects.create(
            nombres="Carlos",
            apellidos="Hernandez",
            sexo="M",
            fecha_nacimiento=nacido(48),
            estado="activo",
            familia=self.familia,
            email="carlos@iglesia.test",
        )
        self.luis = Miembro.objects.create(
            nombres="Luis",
            apellidos="Ramirez",
            sexo="M",
            fecha_nacimiento=nacido(16),
            estado="visitante",
        )
        self.marta = Miembro.objects.create(
            nombres="Marta", apellidos="Ruiz", estado="inactivo"
        )

        MiembroMinisterio.objects.create(miembro=self.ana, ministerio=self.alabanza)
        MiembroMinisterio.objects.create(miembro=self.carlos, ministerio=self.alabanza)
        MiembroMinisterio.objects.create(miembro=self.carlos, ministerio=self.jovenes)

        self.culto = Evento.objects.create(
            nombre="Culto Dominical",
            fecha=self.hoy - timedelta(days=7),
            tipo="culto",
            lugar="Templo",
            hora_inicio="09:00",
            hora_fin="11:00",
            responsable=self.carlos,
        )
        self.ensayo = Evento.objects.create(
            nombre="Ensayo de alabanza",
            fecha=self.hoy - timedelta(days=3),
            tipo="ensayo",
            lugar="Salon",
        )

        Asistencia.objects.create(
            miembro=self.ana, evento=self.culto, fecha=self.culto.fecha, estado="presente"
        )
        Asistencia.objects.create(
            miembro=self.carlos, evento=self.culto, fecha=self.culto.fecha, estado="ausente"
        )
        Asistencia.objects.create(
            miembro=self.ana, evento=self.ensayo, fecha=self.ensayo.fecha, estado="retraso"
        )

        self.guitarra = Equipo.objects.create(
            nombre="Guitarra acustica",
            categoria="instrumento",
            cantidad=3,
            ubicacion="Bodega",
        )
        self.consola = Equipo.objects.create(
            nombre="Consola de sonido",
            categoria="sonido",
            cantidad=1,
            estado="mantenimiento",
        )
        self.proyector = Equipo.objects.create(
            nombre="Proyector",
            categoria="recurso",
            cantidad=2,
            estado="baja",
        )
        self.prestamo = Prestamo.objects.create(
            equipo=self.guitarra,
            miembro=self.ana,
            cantidad=1,
            fecha_prestamo=self.hoy - timedelta(days=2),
            fecha_devolucion_prevista=self.hoy + timedelta(days=5),
        )

    # ---------------------------------------------------------------- apoyo
    def datos_miembro(self, **cambios):
        """POST valido para /miembros/nuevo/."""
        datos = {
            "nombres": "Rosa",
            "apellidos": "Mejia",
            "fecha_nacimiento": "1995-04-12",
            "telefono": "7777-1234",
            "email": "rosa@iglesia.test",
            "direccion": "Colonia Centro",
            "fecha_ingreso": "2026-11-02",
            "estado": "activo",
            "familia": self.familia.pk,
        }
        datos.update(cambios)
        return datos

    def datos_evento(self, **cambios):
        """POST valido para /eventos/nuevo/."""
        datos = {
            "nombre": "Vigilia de oracion",
            "descripcion": "",
            "fecha": "2026-11-20",
            "hora_inicio": "19:00",
            "hora_fin": "21:00",
            "lugar": "Templo",
            "tipo": "vigilia",
            "responsable": self.ana.pk,
        }
        datos.update(cambios)
        return datos

    def datos_prestamo(self, **cambios):
        """POST valido para /inventario/prestamos/."""
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
