"""Vistas del modulo de inventario (Semana 6).

CRUD de equipos, busqueda por nombre o categoria y flujo de
prestamos y devoluciones con control de existencias disponibles.
"""

from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import EquipoForm, PrestamoForm
from .models import Equipo, Prestamo


def _entero(valor):
    """Convierte un id recibido por formulario; None si no es numerico.

    Sin esto, un ``prestamo_id`` de texto termina en ValueError y responde 500
    en vez de 404 (control de errores, Semana 9).
    """
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def lista(request):
    """Listado del inventario con busqueda por nombre o categoria."""
    q = (request.GET.get("q") or "").strip()
    equipos = Equipo.objects.prefetch_related("prestamos")
    if q:
        equipos = equipos.filter(
            Q(nombre__icontains=q) | Q(categoria__icontains=q) | Q(ubicacion__icontains=q)
        )
    return render(
        request, "inventario/lista.html", {"equipos": equipos, "q": q}
    )


def registrar(request):
    """Registrar un nuevo equipo."""
    if request.method == "POST":
        form = EquipoForm(request.POST)
        if form.is_valid():
            equipo = form.save()
            messages.success(request, f"Equipo {equipo.nombre} registrado correctamente.")
            return redirect("inventario:detalle", pk=equipo.pk)
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = EquipoForm()
    return render(
        request,
        "inventario/formulario.html",
        {"form": form, "titulo": "Registrar equipo", "accion": "Guardar"},
    )


def detalle(request, pk):
    """Consulta detallada de un equipo y su historial de prestamos."""
    equipo = get_object_or_404(Equipo, pk=pk)
    prestamos = equipo.prestamos.select_related("miembro")
    return render(
        request, "inventario/detalle.html", {"equipo": equipo, "prestamos": prestamos}
    )


def editar(request, pk):
    """Editar ubicacion, estado, cantidad y demas datos del equipo."""
    equipo = get_object_or_404(Equipo, pk=pk)
    if request.method == "POST":
        form = EquipoForm(request.POST, instance=equipo)
        if form.is_valid():
            equipo = form.save()
            messages.success(request, f"Equipo {equipo.nombre} actualizado correctamente.")
            return redirect("inventario:detalle", pk=equipo.pk)
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = EquipoForm(instance=equipo)
    return render(
        request,
        "inventario/formulario.html",
        {"form": form, "titulo": f"Editar {equipo.nombre}", "accion": "Guardar cambios"},
    )


def prestamos(request):
    """Registro y listado de prestamos de equipos."""
    if request.method == "POST":
        form = PrestamoForm(request.POST)
        if form.is_valid():
            prestamo = form.save()
            messages.success(
                request,
                f"Préstamo registrado: {prestamo.cantidad} x {prestamo.equipo} "
                f"para {prestamo.miembro}.",
            )
            return redirect("inventario:prestamos")
        messages.error(request, "No se pudo registrar el préstamo.")
    else:
        form = PrestamoForm(initial={"fecha_prestamo": timezone.localdate()})
    lista_prestamos = Prestamo.objects.select_related("equipo", "miembro")
    return render(
        request,
        "inventario/prestamos.html",
        {"form": form, "prestamos": lista_prestamos},
    )


def devoluciones(request):
    """Proceso de devolucion de prestamos activos."""
    if request.method == "POST":
        prestamo_id = _entero(request.POST.get("prestamo_id"))
        if prestamo_id is None:
            raise Http404("Préstamo inexistente")
        prestamo = get_object_or_404(Prestamo, pk=prestamo_id)
        if prestamo.estado == "prestado":
            prestamo.estado = "devuelto"
            prestamo.fecha_devolucion_real = timezone.localdate()
            prestamo.save(update_fields=["estado", "fecha_devolucion_real"])
            messages.success(
                request, f"Devolución registrada de {prestamo.cantidad} x {prestamo.equipo}."
            )
        else:
            messages.info(request, "Ese préstamo ya estaba devuelto.")
        return redirect("inventario:devoluciones")
    activos = Prestamo.objects.filter(estado="prestado").select_related("equipo", "miembro")
    return render(request, "inventario/devoluciones.html", {"prestamos": activos})
