"""Exportación de reportes a PDF (reportlab) y Excel (openpyxl) — Semana 8.

Los dos formatos parten del mismo objeto `Reporte`, así que la pantalla, el
PDF y el Excel nunca muestran cifras distintas.
"""

from __future__ import annotations

import io
from datetime import date
from xml.sax.saxutils import escape

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

AZUL = colors.HexColor("#1F4E79")
GRIS = colors.HexColor("#F2F5F9")
VERDE = "#2E7D32"


def nombre_archivo(clave: str, formato: str) -> str:
    return f"reporte_{clave}_{date.today():%Y%m%d}.{formato}"


# ------------------------------------------------------------------------ PDF
def _estilos() -> dict[str, ParagraphStyle]:
    base = "Helvetica"
    return {
        "Titulo": ParagraphStyle(
            "Titulo", fontName=f"{base}-Bold", fontSize=16, leading=20, textColor=AZUL
        ),
        "Texto": ParagraphStyle("Texto", fontName=base, fontSize=9.5, leading=13),
        "Meta": ParagraphStyle(
            "Meta", fontName=base, fontSize=8.5, leading=11, textColor=colors.HexColor("#555555")
        ),
        "Seccion": ParagraphStyle(
            "Seccion", fontName=f"{base}-Bold", fontSize=11, leading=14, textColor=AZUL,
            spaceBefore=4,
        ),
        "Celda": ParagraphStyle("Celda", fontName=base, fontSize=7.4, leading=9.2),
        "CeldaDer": ParagraphStyle(
            "CeldaDer", fontName=base, fontSize=7.4, leading=9.2, alignment=2
        ),
        "Cabecera": ParagraphStyle(
            "Cabecera", fontName=f"{base}-Bold", fontSize=7.4, leading=9.2,
            textColor=colors.white,
        ),
        "CabeceraDer": ParagraphStyle(
            "CabeceraDer", fontName=f"{base}-Bold", fontSize=7.4, leading=9.2,
            textColor=colors.white, alignment=2,
        ),
    }


def _es_numerica(valor: object) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _tabla(cabecera: list[str], filas: list[list], estilos, ancho_total: float):
    """Tabla con celdas que envuelven texto y números alineados a la derecha."""
    numericas = {
        i for i in range(len(cabecera))
        if any(_es_numerica(f[i]) for f in filas if i < len(f))
    }
    encabezado = [
        Paragraph(escape(str(c)), estilos["CabeceraDer" if i in numericas else "Cabecera"])
        for i, c in enumerate(cabecera)
    ]
    cuerpo = []
    for fila in filas:
        cuerpo.append(
            [
                Paragraph(
                    escape(str(v)),
                    estilos["CeldaDer" if i in numericas else "Celda"],
                )
                for i, v in enumerate(fila)
            ]
        )

    n = max(len(cabecera), 1)
    tabla = Table(
        [encabezado] + cuerpo,
        colWidths=[ancho_total / n] * n,
        repeatRows=1,
        hAlign="LEFT",
    )
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), AZUL),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#AAB4C0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return tabla


def _grafico_crecimiento(reporte):
    """Barras de presentes por mes, solo para el reporte de crecimiento."""
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.shapes import Drawing, String

    if reporte.clave != "crecimiento":
        return None
    if not reporte.secciones or not reporte.secciones[0].filas:
        return None
    filas = reporte.secciones[0].filas
    etiquetas = [f[0] for f in filas][-12:]
    valores = [f[3] for f in filas][-12:]
    if not valores:
        return None

    dibujo = Drawing(460, 190)
    dibujo.add(String(0, 178, "Presentes por mes", fontSize=9, fillColor=AZUL))
    barras = VerticalBarChart()
    barras.x, barras.y = 25, 25
    barras.width, barras.height = 420, 140
    barras.data = [valores]
    barras.categoryAxis.categoryNames = etiquetas
    barras.categoryAxis.labels.fontSize = 7
    barras.categoryAxis.labels.angle = 30
    barras.categoryAxis.labels.dx = -4
    barras.categoryAxis.labels.dy = -6
    barras.valueAxis.labels.fontSize = 7
    barras.valueAxis.valueMin = 0
    barras.bars[0].fillColor = colors.HexColor("#2E75B6")
    barras.barWidth = min(0.6, 8 / max(len(valores), 1))
    dibujo.add(barras)
    return dibujo


def _pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#777777"))
    canvas.drawString(1.6 * cm, 1.0 * cm, "Sistema de Gestión - Iglesia Local · Módulo de Reportes")
    canvas.drawRightString(A4[0] - 1.6 * cm, 1.0 * cm, f"Página {doc.page}")
    canvas.restoreState()


def exportar_pdf(reporte) -> bytes:
    buffer = io.BytesIO()
    ancho = A4[0] - 3.2 * cm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title=reporte.titulo,
        author="Sistema de Gestión - Iglesia Local",
        subject="Reporte de la Semana 8",
    )
    estilos = _estilos()
    historia = [
        Paragraph(escape(reporte.titulo), estilos["Titulo"]),
        Spacer(1, 4),
        Paragraph(escape(reporte.descripcion), estilos["Texto"]),
        Spacer(1, 4),
    ]

    if reporte.filtros:
        texto = " · ".join(f"{k}: {v}" for k, v in reporte.filtros.items() if v)
        if texto:
            historia.append(Paragraph(escape(f"Filtros — {texto}"), estilos["Meta"]))
    historia.append(
        Paragraph(f"Generado el {date.today():%d/%m/%Y}", estilos["Meta"])
    )

    if reporte.resumen:
        historia += [Spacer(1, 10), Paragraph("Resumen", estilos["Seccion"]), Spacer(1, 4)]
        historia.append(
            _tabla(
                ["Indicador", "Valor"],
                [[k, v] for k, v in reporte.resumen],
                estilos,
                ancho,
            )
        )

    grafico = _grafico_crecimiento(reporte)
    if grafico is not None:
        historia += [Spacer(1, 10), grafico]

    for seccion in reporte.secciones:
        historia += [Spacer(1, 12), Paragraph(escape(seccion.titulo), estilos["Seccion"]), Spacer(1, 4)]
        if not seccion.filas:
            historia.append(
                Paragraph("Sin datos para los filtros seleccionados.", estilos["Texto"])
            )
            continue
        historia.append(_tabla(seccion.cabecera, seccion.filas, estilos, ancho))

    if reporte.vacio and not reporte.resumen:
        historia.append(Paragraph("Sin datos.", estilos["Texto"]))

    doc.build(historia, onFirstPage=_pie, onLaterPages=_pie)
    return buffer.getvalue()


# ---------------------------------------------------------------------- Excel
_BORDE = Border(
    left=Side(style="thin", color="AAB4C0"),
    right=Side(style="thin", color="AAB4C0"),
    top=Side(style="thin", color="AAB4C0"),
    bottom=Side(style="thin", color="AAB4C0"),
)


def _hoja(wb: Workbook, titulo: str, cabecera: list[str], filas: list[list]):
    nombre = "".join(c for c in titulo if c not in r"[]:*?/\\")[:31] or "Hoja"
    base, i = nombre, 2
    while nombre in wb.sheetnames:
        sufijo = f" ({i})"
        nombre = base[: 31 - len(sufijo)] + sufijo
        i += 1

    ws = wb.create_sheet(nombre)
    ws.cell(row=1, column=1, value=titulo).font = Font(bold=True, size=12, color="1F4E79")
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(len(cabecera), 1))
    ws.row_dimensions[1].height = 20

    for col, valor in enumerate(cabecera, start=1):
        celda = ws.cell(row=3, column=col, value=valor)
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor="1F4E79")
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celda.border = _BORDE

    for fila_idx, fila in enumerate(filas, start=4):
        for col, valor in enumerate(fila, start=1):
            celda = ws.cell(row=fila_idx, column=col, value=valor)
            celda.border = _BORDE
            if isinstance(valor, (int, float)) and not isinstance(valor, bool):
                celda.alignment = Alignment(horizontal="right")
            else:
                celda.alignment = Alignment(vertical="top", wrap_text=True)

    ultima = 3 + len(filas)
    if filas:
        ws.auto_filter.ref = f"A3:{get_column_letter(len(cabecera))}{ultima}"
    ws.freeze_panes = "A4"

    for col in range(1, len(cabecera) + 1):
        largo = max(
            [len(str(cabecera[col - 1]))]
            + [len(str(f[col - 1])) for f in filas if col - 1 < len(f)]
        )
        ws.column_dimensions[get_column_letter(col)].width = min(max(largo + 2, 11), 46)
    return ws


def exportar_xlsx(reporte) -> bytes:
    wb = Workbook()
    resumen = wb.active
    resumen.title = "Resumen"

    resumen.cell(row=1, column=1, value=reporte.titulo).font = Font(
        bold=True, size=14, color="1F4E79"
    )
    resumen.merge_cells(start_row=1, start_column=1, end_row=1, end_column=2)
    resumen.row_dimensions[1].height = 24

    resumen.cell(row=3, column=1, value=reporte.descripcion).alignment = Alignment(wrap_text=True)
    resumen.merge_cells(start_row=3, start_column=1, end_row=3, end_column=2)
    resumen.row_dimensions[3].height = 42

    fila = 5
    if reporte.filtros:
        texto = " · ".join(f"{k}: {v}" for k, v in reporte.filtros.items() if v)
        if texto:
            resumen.cell(row=fila, column=1, value=f"Filtros: {texto}").font = Font(italic=True)
            fila += 1
    resumen.cell(row=fila, column=1, value=f"Generado el {date.today():%d/%m/%Y}").font = Font(
        italic=True, color="777777"
    )
    fila += 2

    if reporte.resumen:
        for col, valor in enumerate(("Indicador", "Valor"), start=1):
            celda = resumen.cell(row=fila, column=col, value=valor)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill("solid", fgColor="1F4E79")
            celda.border = _BORDE
        fila += 1
        for etiqueta, valor in reporte.resumen:
            resumen.cell(row=fila, column=1, value=etiqueta).border = _BORDE
            celda = resumen.cell(row=fila, column=2, value=valor)
            celda.border = _BORDE
            celda.alignment = Alignment(horizontal="right" if isinstance(valor, (int, float)) else "left")
            fila += 1

    resumen.column_dimensions["A"].width = 42
    resumen.column_dimensions["B"].width = 30

    for seccion in reporte.secciones:
        _hoja(wb, seccion.titulo, seccion.cabecera, seccion.filas)

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
