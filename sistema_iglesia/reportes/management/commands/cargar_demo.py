"""Carga datos de demostración para los reportes (Semana 8).

    python manage.py cargar_demo
    python manage.py cargar_demo --limpiar

Crea un conjunto pequeño y realista (12 miembros, 4 familias, 4 ministerios
y los eventos de agosto a octubre de 2026 con sus asistencias) para que los
reportes tengan algo que mostrar en la presentación.

Es idempotente: se puede correr varias veces sin duplicar. Todo lo que crea
queda marcado (miembros con correo @demo.local y eventos con la descripción
"Evento de demostración") para poder retirarlo con `--limpiar`.
"""

import random
from datetime import date, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from eventos.models import Asistencia, Evento
from miembros.models import Familia, Miembro, MiembroMinisterio, Ministerio

MARCA = "Evento de demostración (Semana 8)"
CORREO_DEMO = "@demo.local"

FAMILIAS = ["Hernández", "López", "Martínez", "Cruz"]

MINISTERIOS = ["Alabanza", "Sonido", "Niños", "Intercesión"]

MIEMBROS = [
    # nombres, apellidos, sexo, nacimiento, estado, familia, ministerios
    ("Ana", "Hernández", "F", date(1990, 5, 10), "activo", "Hernández", ["Alabanza"]),
    ("Carlos", "Hernández", "M", date(1975, 3, 2), "activo", "Hernández", ["Alabanza", "Sonido"]),
    ("María", "López", "F", date(1985, 7, 22), "activo", "López", ["Niños"]),
    ("José", "López", "M", date(1982, 11, 30), "activo", "López", ["Sonido"]),
    ("Sofía", "López", "F", date(2012, 4, 18), "activo", "López", ["Niños"]),
    ("Pedro", "Martínez", "M", date(1998, 9, 5), "activo", "Martínez", ["Intercesión"]),
    ("Rosa", "Martínez", "F", date(2001, 2, 14), "activo", "Martínez", ["Alabanza"]),
    ("Daniel", "Cruz", "M", date(1965, 12, 1), "activo", "Cruz", ["Intercesión"]),
    ("Elena", "Cruz", "F", date(1968, 6, 20), "activo", "Cruz", ["Niños"]),
    ("Luis", "Ramírez", "M", date(2010, 1, 15), "visitante", None, []),
    ("Miguel Ángel", "Torres", "M", date(1995, 3, 11), "inactivo", None, []),
    ("Carmen", "Torres", "F", date(1993, 8, 25), "activo", None, ["Alabanza"]),
]


def _domingos(desde: date, hasta: date):
    dia = desde
    while dia <= hasta:
        if dia.weekday() == 6:
            yield dia
        dia += timedelta(days=1)


class Command(BaseCommand):
    help = "Carga (o retira) datos de demostración para los reportes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar", action="store_true", help="retira los datos de demostración"
        )

    def handle(self, *args, **opciones):
        if opciones["limpiar"]:
            self._limpiar()
            return
        with transaction.atomic():
            self._cargar()
        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados"))

    # ------------------------------------------------------------------
    def _limpiar(self):
        eventos = Evento.objects.filter(descripcion=MARCA)
        Asistencia.objects.filter(evento__in=eventos).delete()
        eventos.delete()

        miembros = Miembro.objects.filter(email__endswith=CORREO_DEMO)
        Asistencia.objects.filter(miembro__in=miembros).delete()
        miembro_ids = list(miembros.values_list("id", flat=True))
        MiembroMinisterio.objects.filter(miembro_id__in=miembro_ids).delete()
        miembros.delete()

        Familia.objects.filter(nombre_familia__in=FAMILIAS, miembros__isnull=True).delete()
        Ministerio.objects.filter(nombre__in=MINISTERIOS, miembros__isnull=True).delete()
        self.stdout.write(self.style.SUCCESS("Datos de demostración retirados"))

    # ------------------------------------------------------------------
    def _cargar(self):
        familias = {
            nombre: Familia.objects.get_or_create(nombre_familia=nombre)[0]
            for nombre in FAMILIAS
        }
        ministerios = {
            nombre: Ministerio.objects.get_or_create(nombre=nombre)[0]
            for nombre in MINISTERIOS
        }

        miembros = []
        for i, (nombres, apellidos, sexo, nacimiento, estado, familia, mins) in enumerate(MIEMBROS, start=1):
            miembro, _ = Miembro.objects.update_or_create(
                nombres=nombres,
                apellidos=apellidos,
                defaults={
                    "sexo": sexo,
                    "fecha_nacimiento": nacimiento,
                    "estado": estado,
                    "familia": familias.get(familia) if familia else None,
                    "email": f"demo{i:02d}{CORREO_DEMO}",
                    "fecha_ingreso": date(2020, 1, 1) + timedelta(days=90 * i),
                },
            )
            miembros.append(miembro)
            MiembroMinisterio.objects.filter(miembro=miembro).delete()
            for nombre in mins:
                MiembroMinisterio.objects.create(
                    miembro=miembro, ministerio=ministerios[nombre]
                )

        activos = [m for m in miembros if m.estado == "activo"]

        eventos = []
        for fecha in _domingos(date(2026, 8, 2), date(2026, 10, 25)):
            eventos.append((fecha, "Culto Dominical", "culto", time(9, 0), time(11, 0)))
        for fecha in [date(2026, 8, 6), date(2026, 8, 20), date(2026, 9, 3),
                      date(2026, 9, 17), date(2026, 10, 1), date(2026, 10, 15)]:
            eventos.append((fecha, "Ensayo de alabanza", "ensayo", time(18, 0), time(20, 0)))
        for fecha in [date(2026, 8, 15), date(2026, 9, 19), date(2026, 10, 17)]:
            eventos.append((fecha, "Reunión de jóvenes", "jóvenes", time(17, 0), time(19, 0)))
        eventos.append((date(2026, 10, 30), "Vigilia de oración", "vigilia", time(19, 0), time(22, 0)))

        azar = random.Random(2026)

        for fecha, nombre, tipo, inicio, fin in eventos:
            evento, _ = Evento.objects.get_or_create(
                nombre=nombre,
                fecha=fecha,
                defaults={
                    "tipo": tipo,
                    "hora_inicio": inicio,
                    "hora_fin": fin,
                    "lugar": "Templo principal",
                    "descripcion": MARCA,
                    "responsable": miembros[1],
                },
            )
            if evento.descripcion != MARCA:
                evento.descripcion = MARCA
                evento.save(update_fields=["descripcion"])

            # Asistencia: los activos son la base; los visitantes aparecen a veces.
            convocados = list(activos)
            if nombre == "Reunión de jóvenes":
                convocados = [m for m in activos if m.fecha_nacimiento.year > 1985]
            elif nombre == "Ensayo de alabanza":
                convocados = [
                    m for m in activos
                    if m.miembroministerio_set.filter(ministerio__nombre="Alabanza").exists()
                    or m.miembroministerio_set.filter(ministerio__nombre="Sonido").exists()
                ]
            if nombre == "Culto Dominical" and azar.random() < 0.35:
                convocados.append(miembros[9])  # el visitante a veces llega

            for miembro in convocados:
                if azar.random() < 0.08:
                    continue  # no se le tomó asistencia
                estado = azar.choices(
                    ["presente", "retraso", "justificado", "ausente"],
                    weights=[82, 8, 5, 5],
                )[0]
                Asistencia.objects.update_or_create(
                    miembro=miembro,
                    evento=evento,
                    defaults={"fecha": fecha, "estado": estado},
                )
