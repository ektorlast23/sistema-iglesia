"""Consultas agregadas del modulo de reportes (Semana 8).

Cada funcion devuelve un `Reporte`: un titulo, un resumen de indicadores y
una o varias secciones con cabecera y filas, listas para mostrarse en
pantalla o exportarse a PDF/Excel.

Las consultas se escriben con el ORM (agregados con `filter=`) porque el
sistema corre en MySQL 8 y las pruebas en SQLite; el equivalente en SQL puro
queda documentado en `reportes/sql/reportes.sql`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from eventos.models import Asistencia, Evento
from inventario.models import Equipo, Prestamo
from miembros.models import Miembro, Ministerio


# --------------------------------------------------------------------- modelo
@dataclass
class Seccion:
    """Una tabla del reporte."""

    titulo: str
    cabecera: list[str]
    filas: list[list[Any]]


@dataclass
class Reporte:
    """Reporte completo, independiente de como se presente."""

    clave: str
    titulo: str
    descripcion: str
    filtros: dict[str, str] = field(default_factory=dict)
    resumen: list[tuple[str, Any]] = field(default_factory=list)
    secciones: list[Seccion] = field(default_factory=list)

    @property
    def vacio(self) -> bool:
        return all(not s.filas for s in self.secciones)


def a_fecha(valor: str | None) -> date | None:
    """Convierte 'AAAA-MM-DD' en fecha; cualquier otra cosa se ignora."""
    try:
        return date.fromisoformat((valor or "").strip())
    except ValueError:
        return None


def _pct(parte: int, total: int) -> float:
    return round((parte / total) * 100, 1) if total else 0.0


# ------------------------------------------------------- 1. asistencia x evento
def asistencia_por_evento(
    desde: date | None = None,
    hasta: date | None = None,
    tipo: str = "",
) -> Reporte:
    """Asistencias de cada evento con el desglose por estado."""
    eventos = Evento.objects.all()
    if desde:
        eventos = eventos.filter(fecha__gte=desde)
    if hasta:
        eventos = eventos.filter(fecha__lte=hasta)
    if tipo:
        eventos = eventos.filter(tipo=tipo)

    eventos = eventos.annotate(
        presentes=Count("asistencias", filter=Q(asistencias__estado="presente")),
        ausentes=Count("asistencias", filter=Q(asistencias__estado="ausente")),
        justificados=Count("asistencias", filter=Q(asistencias__estado="justificado")),
        retrasos=Count("asistencias", filter=Q(asistencias__estado="retraso")),
        total=Count("asistencias"),
    ).order_by("-fecha", "nombre")

    filas = []
    for e in eventos:
        filas.append(
            [
                e.nombre,
                f"{e.fecha:%d/%m/%Y}",
                e.tipo or "—",
                e.presentes,
                e.ausentes,
                e.justificados,
                e.retrasos,
                e.total,
                f"{_pct(e.presentes, e.total):.1f} %",
            ]
        )

    total_asistencias = sum(f[7] for f in filas)
    total_presentes = sum(f[3] for f in filas)
    n_eventos = len(filas)
    promedio = round(total_presentes / n_eventos, 1) if n_eventos else 0

    resumen = [
        ("Eventos en el periodo", n_eventos),
        ("Asistencias registradas", total_asistencias),
        ("Asistencias presentes", total_presentes),
        ("Promedio de presentes por evento", promedio),
    ]
    if total_asistencias:
        resumen.append(("Porcentaje de asistencia", f"{_pct(total_presentes, total_asistencias):.1f} %"))

    return Reporte(
        clave="asistencia",
        titulo="Asistencia por evento",
        descripcion=(
            "Desglose de asistencias por evento y estado (presente, ausente, "
            "justificado y retraso), con el porcentaje de asistencia de cada evento."
        ),
        filtros=_filtros(desde, hasta, tipo),
        resumen=resumen,
        secciones=[
            Seccion(
                "Detalle por evento",
                [
                    "Evento",
                    "Fecha",
                    "Tipo",
                    "Presentes",
                    "Ausentes",
                    "Justificados",
                    "Retrasos",
                    "Total",
                    "% asistencia",
                ],
                filas,
            )
        ],
    )


# ------------------------------------------------- 2. crecimiento y concurrencia
def crecimiento_asistencia(
    desde: date | None = None, hasta: date | None = None
) -> Reporte:
    """Serie mensual de asistencias y los eventos mas concurridos."""
    registros = Asistencia.objects.all()
    eventos = Evento.objects.all()
    if desde:
        registros = registros.filter(evento__fecha__gte=desde)
        eventos = eventos.filter(fecha__gte=desde)
    if hasta:
        registros = registros.filter(evento__fecha__lte=hasta)
        eventos = eventos.filter(fecha__lte=hasta)

    mensual = (
        registros.annotate(mes=TruncMonth("evento__fecha"))
        .values("mes")
        .annotate(
            n_eventos=Count("evento", distinct=True),
            total=Count("id"),
            presentes=Count("id", filter=Q(estado="presente")),
        )
        .order_by("mes")
    )

    filas_mes = []
    for m in mensual:
        mes = m["mes"]
        etiqueta = f"{mes:%m/%Y}" if mes else "Sin fecha"
        filas_mes.append(
            [
                etiqueta,
                m["n_eventos"],
                m["total"],
                m["presentes"],
                f"{_pct(m['presentes'], m['total']):.1f} %",
                round(m["presentes"] / m["n_eventos"], 1) if m["n_eventos"] else 0,
            ]
        )

    variacion = ""
    if len(filas_mes) >= 2 and filas_mes[-2][3]:
        anterior, actual = filas_mes[-2][3], filas_mes[-1][3]
        variacion = f"{(actual - anterior) / anterior * 100:+.1f} %"

    top = (
        eventos.annotate(
            presentes=Count("asistencias", filter=Q(asistencias__estado="presente")),
            total=Count("asistencias"),
        )
        .filter(total__gt=0)
        .order_by("-presentes", "-total", "fecha")[:10]
    )

    filas_top = [
        [
            posicion,
            e.nombre,
            f"{e.fecha:%d/%m/%Y}",
            e.tipo or "—",
            e.presentes,
            e.total,
            f"{_pct(e.presentes, e.total):.1f} %",
        ]
        for posicion, e in enumerate(top, start=1)
    ]

    resumen = [
        ("Meses con registro", len(filas_mes)),
        ("Eventos con asistencia", eventos.filter(asistencias__isnull=False).distinct().count()),
        ("Presentes en el periodo", sum(f[3] for f in filas_mes)),
    ]
    if variacion:
        resumen.append(("Variación del último mes", variacion))

    return Reporte(
        clave="crecimiento",
        titulo="Crecimiento de la asistencia",
        descripcion=(
            "Evolución mensual de las asistencias y presentes, más el ranking de "
            "los eventos con más participación."
        ),
        filtros=_filtros(desde, hasta),
        resumen=resumen,
        secciones=[
            Seccion(
                "Serie mensual",
                ["Mes", "Eventos", "Asistencias", "Presentes", "% asistencia", "Presentes/evento"],
                filas_mes,
            ),
            Seccion(
                "Eventos más concurridos",
                ["#", "Evento", "Fecha", "Tipo", "Presentes", "Total", "% asistencia"],
                filas_top,
            ),
        ],
    )


# --------------------------------------------------------- 3. estado inventario
def inventario() -> Reporte:
    """Disponibilidad por categoria y prestamos que siguen afuera."""
    totales = {
        t["categoria"]: t
        for t in Equipo.objects.values("categoria").annotate(
            equipos=Count("id"),
            unidades=Sum("cantidad"),
            mantenimiento=Sum("cantidad", filter=Q(estado="mantenimiento")),
            baja=Sum("cantidad", filter=Q(estado="baja")),
        )
    }
    prestadas = {
        p["equipo__categoria"]: p["unidades"]
        for p in Prestamo.objects.filter(estado="prestado")
        .values("equipo__categoria")
        .annotate(unidades=Sum("cantidad"))
    }

    filas = []
    for categoria, etiqueta in Equipo.CATEGORIA_CHOICES:
        t = totales.get(categoria, {})
        unidades = t.get("unidades") or 0
        en_prestamo = prestadas.get(categoria, 0) or 0
        de_baja = t.get("baja") or 0
        disponibles = max(unidades - en_prestamo - de_baja, 0)
        filas.append(
            [
                etiqueta,
                t.get("equipos") or 0,
                unidades,
                en_prestamo,
                disponibles,
                t.get("mantenimiento") or 0,
                de_baja,
            ]
        )

    hoy = timezone.localdate()
    activos = Prestamo.objects.filter(estado="prestado").select_related(
        "equipo", "miembro"
    ).order_by("fecha_devolucion_prevista")

    filas_prestamos = []
    atrasados = 0
    for p in activos:
        dias = (hoy - p.fecha_devolucion_prevista).days
        if dias > 0:
            atrasados += 1
            situacion = f"Atrasado {dias} día(s)"
        else:
            situacion = "En plazo"
        filas_prestamos.append(
            [
                p.equipo.nombre,
                str(p.miembro),
                p.cantidad,
                f"{p.fecha_prestamo:%d/%m/%Y}",
                f"{p.fecha_devolucion_prevista:%d/%m/%Y}",
                situacion,
            ]
        )

    unidades_totales = sum(f[2] for f in filas)
    en_prestamo_total = sum(f[3] for f in filas)

    return Reporte(
        clave="inventario",
        titulo="Estado del inventario",
        descripcion=(
            "Unidades por categoría, disponibilidad calculada (total menos préstamos "
            "activos y bajas) y control de los préstamos que siguen sin devolverse."
        ),
        resumen=[
            ("Equipos registrados", sum(f[1] for f in filas)),
            ("Unidades totales", unidades_totales),
            ("Unidades en préstamo", en_prestamo_total),
            ("Unidades disponibles", sum(f[4] for f in filas)),
            ("Préstamos activos", len(filas_prestamos)),
            ("Préstamos atrasados", atrasados),
        ],
        secciones=[
            Seccion(
                "Disponibilidad por categoría",
                [
                    "Categoría",
                    "Equipos",
                    "Unidades",
                    "En préstamo",
                    "Disponibles",
                    "En mantenimiento",
                    "De baja",
                ],
                filas,
            ),
            Seccion(
                "Préstamos activos",
                ["Equipo", "Miembro", "Cantidad", "Prestado", "Devolución prevista", "Situación"],
                filas_prestamos,
            ),
        ],
    )


# ------------------------------------------------------------- 4. demografia
RANGOS_EDAD = [
    ("Menores de 18", 0, 17),
    ("18 a 25 años", 18, 25),
    ("26 a 35 años", 26, 35),
    ("36 a 45 años", 36, 45),
    ("46 a 60 años", 46, 60),
    ("Mayores de 60", 61, 200),
]


def demografia() -> Reporte:
    """Composición de la membresía: estado, sexo, edad, familia y ministerio."""
    miembros = Miembro.objects.all()
    total = miembros.count()

    por_estado = miembros.values("estado").annotate(n=Count("id")).order_by("-n")
    etiquetas_estado = dict(Miembro.ESTADO_CHOICES)
    filas_estado = [
        [etiquetas_estado.get(f["estado"], f["estado"]), f["n"], f"{_pct(f['n'], total):.1f} %"]
        for f in por_estado
    ]

    por_sexo = miembros.values("sexo").annotate(n=Count("id")).order_by("-n")
    etiquetas_sexo = dict(Miembro.SEXO_CHOICES)
    filas_sexo = [
        [etiquetas_sexo.get(f["sexo"], "Sin dato") if f["sexo"] else "Sin dato",
         f["n"], f"{_pct(f['n'], total):.1f} %"]
        for f in por_sexo
    ]

    hoy = timezone.localdate()
    conteo_edad = {etiqueta: 0 for etiqueta, _, _ in RANGOS_EDAD}
    sin_fecha = 0
    for nacimiento in miembros.values_list("fecha_nacimiento", flat=True):
        if not nacimiento:
            sin_fecha += 1
            continue
        edad = hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))
        for etiqueta, minimo, maximo in RANGOS_EDAD:
            if minimo <= edad <= maximo:
                conteo_edad[etiqueta] += 1
                break

    filas_edad = [
        [etiqueta, n, f"{_pct(n, total):.1f} %"] for etiqueta, n in conteo_edad.items()
    ]
    if sin_fecha:
        filas_edad.append(["Sin fecha de nacimiento", sin_fecha, f"{_pct(sin_fecha, total):.1f} %"])

    por_familia = (
        miembros.values("familia__nombre_familia")
        .annotate(n=Count("id"))
        .order_by("-n", "familia__nombre_familia")[:10]
    )
    filas_familia = [
        [f["familia__nombre_familia"] or "Sin familia", f["n"], f"{_pct(f['n'], total):.1f} %"]
        for f in por_familia
    ]

    por_ministerio = Ministerio.objects.annotate(
        n=Count("miembros", distinct=True),
        activos=Count("miembros", filter=Q(miembros__estado="activo"), distinct=True),
    ).order_by("-n", "nombre")
    filas_ministerio = [
        [m.nombre, m.n, m.activos, f"{_pct(m.n, total):.1f} %"] for m in por_ministerio
    ]

    activos = miembros.filter(estado="activo").count()
    con_familia = miembros.filter(familia__isnull=False).count()
    en_ministerio = miembros.filter(ministerios__isnull=False).distinct().count()

    return Reporte(
        clave="demografia",
        titulo="Datos demográficos de la membresía",
        descripcion=(
            "Composición de los miembros por estado, sexo y rango de edad, y su "
            "distribución por familia y ministerio."
        ),
        resumen=[
            ("Miembros registrados", total),
            ("Miembros activos", activos),
            ("Miembros con familia asignada", con_familia),
            ("Miembros en algún ministerio", en_ministerio),
        ],
        secciones=[
            Seccion("Por estado", ["Estado", "Miembros", "% del total"], filas_estado),
            Seccion("Por sexo", ["Sexo", "Miembros", "% del total"], filas_sexo),
            Seccion("Por rango de edad", ["Rango", "Miembros", "% del total"], filas_edad),
            Seccion("Familias con más miembros", ["Familia", "Miembros", "% del total"], filas_familia),
            Seccion(
                "Participación por ministerio",
                ["Ministerio", "Miembros", "Activos", "% del total"],
                filas_ministerio,
            ),
        ],
    )


# --------------------------------------------------------------------- apoyo
def _filtros(desde: date | None, hasta: date | None, tipo: str = "") -> dict[str, str]:
    filtros: dict[str, str] = {}
    if desde:
        filtros["Desde"] = f"{desde:%d/%m/%Y}"
    if hasta:
        filtros["Hasta"] = f"{hasta:%d/%m/%Y}"
    if tipo:
        filtros["Tipo de evento"] = tipo
    return filtros


CATALOGO = {
    "asistencia": ("Asistencia por evento", asistencia_por_evento),
    "crecimiento": ("Crecimiento de la asistencia", crecimiento_asistencia),
    "inventario": ("Estado del inventario", inventario),
    "demografia": ("Datos demográficos", demografia),
}
