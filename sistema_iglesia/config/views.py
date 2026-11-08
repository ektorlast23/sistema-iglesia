"""Panel de control del sistema (ajuste posterior a la Semana 9).

La portada deja de ser una lista de enlaces y pasa a mostrar el estado real de
la iglesia: cuántos miembros activos hay, cuántos eventos y asistencias se
registraron, cuántas unidades de inventario están disponibles y qué préstamos
siguen afuera. Todas las cifras salen de la base, sin datos quemados.
"""

from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from eventos.models import Asistencia, Evento
from inventario.models import Equipo, Prestamo
from miembros.models import Miembro


@require_GET
def home(request):
    """Resumen general con accesos directos a los cuatro módulos."""
    hoy = timezone.localdate()

    equipos = Equipo.objects.prefetch_related("prestamos")
    prestamos_activos = Prestamo.objects.filter(estado="prestado")

    contexto = {
        "hoy": hoy,
        "miembros_activos": Miembro.objects.filter(estado="activo").count(),
        "miembros_total": Miembro.objects.count(),
        "eventos_total": Evento.objects.count(),
        "asistencias_total": Asistencia.objects.count(),
        "equipos_total": equipos.count(),
        "unidades_disponibles": sum(e.cantidad_disponible for e in equipos),
        "prestamos_activos": prestamos_activos.count(),
        "prestamos_atrasados": prestamos_activos.filter(
            fecha_devolucion_prevista__lt=hoy
        ).count(),
        "ultimos_eventos": Evento.objects.order_by("-fecha", "-hora_inicio")[:5],
        "prestamos": prestamos_activos.select_related("equipo", "miembro").order_by(
            "fecha_devolucion_prevista"
        )[:5],
    }
    return render(request, "home.html", contexto)
