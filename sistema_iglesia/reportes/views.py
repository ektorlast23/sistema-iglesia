"""Vistas del módulo de reportes (Semana 8).

Cuatro reportes sobre la misma base de datos:

* asistencia por evento, con desglose por estado;
* crecimiento mensual y eventos más concurridos;
* estado del inventario y préstamos activos;
* datos demográficos de la membresía.

Cada uno se muestra en pantalla y se puede descargar en PDF o Excel.
"""

from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from eventos.models import Asistencia, Evento
from inventario.models import Equipo
from miembros.models import Miembro

from . import consultas
from .exportar import exportar_pdf, exportar_xlsx, nombre_archivo

FORMATOS = {
    "pdf": ("application/pdf", exportar_pdf),
    "xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        exportar_xlsx,
    ),
}

DESCRIPCIONES = {
    "asistencia": "Asistencias de cada evento con desglose por estado y porcentaje de participación.",
    "crecimiento": "Evolución mensual de la asistencia y ranking de eventos más concurridos.",
    "inventario": "Disponibilidad por categoría, unidades en préstamo y préstamos atrasados.",
    "demografia": "Miembros por estado, sexo, edad, familia y ministerio.",
}

CON_FILTROS = {"asistencia", "crecimiento"}


def _reporte(clave: str, request) -> consultas.Reporte:
    """Construye el reporte pedido con los filtros de la URL."""
    if clave not in consultas.CATALOGO:
        raise Http404(f"El reporte '{clave}' no existe")

    desde = consultas.a_fecha(request.GET.get("desde"))
    hasta = consultas.a_fecha(request.GET.get("hasta"))

    if clave == "asistencia":
        tipo = (request.GET.get("tipo") or "").strip()
        return consultas.asistencia_por_evento(desde=desde, hasta=hasta, tipo=tipo)
    if clave == "crecimiento":
        return consultas.crecimiento_asistencia(desde=desde, hasta=hasta)
    return consultas.CATALOGO[clave][1]()


def indice(request):
    """Panel de entrada con los cuatro reportes y cifras generales."""
    return render(
        request,
        "reportes/indice.html",
        {
            "reportes": [
                {
                    "clave": clave,
                    "titulo": titulo,
                    "descripcion": DESCRIPCIONES[clave],
                }
                for clave, (titulo, _) in consultas.CATALOGO.items()
            ],
            "totales": {
                "miembros": Miembro.objects.count(),
                "eventos": Evento.objects.count(),
                "asistencias": Asistencia.objects.count(),
                "equipos": Equipo.objects.count(),
            },
        },
    )


def detalle(request, clave: str):
    """Vista en pantalla de un reporte con su formulario de filtros."""
    reporte = _reporte(clave, request)
    tipos = (
        Evento.objects.exclude(tipo__isnull=True)
        .exclude(tipo="")
        .values_list("tipo", flat=True)
        .distinct()
        .order_by("tipo")
    )
    return render(
        request,
        "reportes/detalle.html",
        {
            "reporte": reporte,
            "clave": clave,
            "con_filtros": clave in CON_FILTROS,
            "tipos": tipos,
            "desde": (request.GET.get("desde") or "").strip(),
            "hasta": (request.GET.get("hasta") or "").strip(),
            "tipo": (request.GET.get("tipo") or "").strip(),
        },
    )


def exportar(request, clave: str, formato: str):
    """Descarga el reporte en PDF o Excel."""
    if formato not in FORMATOS:
        return HttpResponseBadRequest("Formato no soportado: use pdf o xlsx")

    reporte = _reporte(clave, request)
    tipo_mime, generador = FORMATOS[formato]
    contenido = generador(reporte)

    respuesta = HttpResponse(contenido, content_type=tipo_mime)
    respuesta["Content-Disposition"] = (
        f'attachment; filename="{nombre_archivo(reporte.clave, formato)}"'
    )
    return respuesta
