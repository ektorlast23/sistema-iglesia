"""Vistas del modulo de miembros (Semana 5): CRUD completo.

La eliminacion es una baja logica: pone estado='inactivo' en vez de
borrar la fila, porque futuros modulos (eventos, asistencias) se
relacionaran con los miembros.
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MiembroForm
from .models import Miembro


def lista(request):
    """Consultar: tabla con todos los miembros registrados."""
    miembros = Miembro.objects.select_related("familia").order_by("apellidos", "nombres")
    return render(request, "miembros/lista.html", {"miembros": miembros})


def registrar(request):
    """Registrar: alta de un nuevo miembro con validacion del formulario."""
    if request.method == "POST":
        form = MiembroForm(request.POST)
        if form.is_valid():
            miembro = form.save()
            messages.success(
                request, f"Miembro {miembro} registrado correctamente."
            )
            return redirect("miembros:detalle", pk=miembro.pk)
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = MiembroForm()
    return render(
        request,
        "miembros/formulario.html",
        {"form": form, "titulo": "Registrar miembro", "accion": "Guardar"},
    )


def detalle(request, pk):
    """Ver detalles: informacion individual de un miembro."""
    miembro = get_object_or_404(Miembro.objects.select_related("familia"), pk=pk)
    return render(request, "miembros/detalle.html", {"miembro": miembro})


def editar(request, pk):
    """Editar: actualizar los datos de un miembro existente."""
    miembro = get_object_or_404(Miembro, pk=pk)
    if request.method == "POST":
        form = MiembroForm(request.POST, instance=miembro)
        if form.is_valid():
            miembro = form.save()
            messages.success(
                request, f"Datos de {miembro} actualizados correctamente."
            )
            return redirect("miembros:detalle", pk=miembro.pk)
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = MiembroForm(instance=miembro)
    return render(
        request,
        "miembros/formulario.html",
        {"form": form, "titulo": f"Editar a {miembro}", "accion": "Guardar cambios"},
    )


def eliminar(request, pk):
    """Eliminar: baja logica con pantalla de confirmacion previa."""
    miembro = get_object_or_404(Miembro, pk=pk)
    if request.method == "POST":
        miembro.estado = "inactivo"
        miembro.save(update_fields=["estado"])
        messages.success(
            request, f"{miembro} dado de baja (ahora inactivo)."
        )
        return redirect("miembros:lista")
    return render(request, "miembros/confirmar_eliminacion.html", {"miembro": miembro})
