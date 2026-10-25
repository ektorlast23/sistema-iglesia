"""Vistas del modulo de eventos (Semana 7).

CRUD de eventos, registro de asistencia por evento y consulta del
historial de asistencias por miembro.
"""

from datetime import date

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from miembros.models import Miembro

from .forms import AsistenciaEditarForm, AsistenciaForm, EventoForm
from .models import Asistencia, Evento


def lista(request):
    """Listado de eventos con busqueda por nombre, lugar o tipo."""
    q = (request.GET.get("q") or "").strip()
    eventos = Evento.objects.select_related("responsable").order_by(
        "-fecha", "hora_inicio"
    )
    if q:
        eventos = eventos.filter(
            Q(nombre__icontains=q) | Q(lugar__icontains=q) | Q(tipo__icontains=q)
        )
    return render(request, "eventos/lista.html", {"eventos": eventos, "q": q})


def registrar(request):
    """Registrar un nuevo evento."""
    if request.method == "POST":
        form = EventoForm(request.POST)
        if form.is_valid():
            evento = form.save()
            messages.success(request, f"Evento {evento.nombre} registrado correctamente.")
            return redirect("eventos:lista")
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = EventoForm()
    return render(
        request,
        "eventos/formulario.html",
        {"form": form, "titulo": "Registrar evento", "accion": "Guardar"},
    )


def detalle(request, pk):
    """Consulta detallada de un evento y sus asistencias."""
    evento = get_object_or_404(Evento.objects.select_related("responsable"), pk=pk)
    asistencias = evento.asistencias.select_related("miembro").order_by(
        "miembro__apellidos", "miembro__nombres"
    )
    total_asistentes = asistencias.count()
    return render(
        request,
        "eventos/detalle.html",
        {
            "evento": evento,
            "asistencias": asistencias,
            "total_asistentes": total_asistentes,
            "total": total_asistentes,
        },
    )


def editar(request, pk):
    """Editar los datos de un evento existente."""
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == "POST":
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            evento = form.save()
            messages.success(request, f"Evento {evento.nombre} actualizado correctamente.")
            return redirect("eventos:detalle", pk=evento.pk)
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = EventoForm(instance=evento)
    return render(
        request,
        "eventos/formulario.html",
        {"form": form, "titulo": f"Editar {evento.nombre}", "accion": "Guardar cambios"},
    )


def eliminar(request, pk):
    """Eliminar un evento con pantalla de confirmacion previa."""
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == "POST":
        nombre = evento.nombre
        evento.delete()
        messages.success(request, f"Evento {nombre} eliminado correctamente.")
        return redirect("eventos:lista")
    return render(
        request, "eventos/confirmar_eliminacion.html", {"evento": evento}
    )


def asistencia_registrar(request, evento_id):
    """Registrar la asistencia de un miembro a un evento."""
    evento = get_object_or_404(Evento, pk=evento_id)
    if request.method == "POST":
        form = AsistenciaForm(request.POST)
        if form.is_valid():
            asistencia = form.save()
            messages.success(
                request,
                f"Asistencia registrada para {asistencia.miembro} en {evento.nombre}.",
            )
            return redirect("eventos:detalle", pk=evento.pk)
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = AsistenciaForm(initial={"evento": evento, "fecha": date.today()})
    return render(
        request,
        "eventos/asistencia_form.html",
        {"form": form, "evento": evento, "accion": "Guardar"},
    )


def lista_asistencias(request, evento_id):
    """Listar las asistencias registradas para un evento."""
    evento = get_object_or_404(Evento, pk=evento_id)
    asistencias = Asistencia.objects.filter(evento=evento).select_related(
        "miembro"
    ).order_by("miembro__apellidos", "miembro__nombres")
    total_asistentes = asistencias.count()
    return render(
        request,
        "eventos/asistencias_lista.html",
        {
            "evento": evento,
            "asistencias": asistencias,
            "total_asistentes": total_asistentes,
            "total": total_asistentes,
        },
    )


def asistencia_editar(request, pk):
    """Editar el estado y las observaciones de una asistencia."""
    asistencia = get_object_or_404(
        Asistencia.objects.select_related("miembro", "evento"), pk=pk
    )
    if request.method == "POST":
        form = AsistenciaEditarForm(request.POST, instance=asistencia)
        if form.is_valid():
            form.save()
            messages.success(request, "Asistencia actualizada correctamente.")
            return redirect(
                "eventos:lista_asistencias", evento_id=asistencia.evento_id
            )
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = AsistenciaEditarForm(instance=asistencia)
    return render(
        request,
        "eventos/asistencia_editar.html",
        {"form": form, "asistencia": asistencia, "accion": "Guardar cambios"},
    )


def asistencia_consulta_miembro(request):
    """Consultar el historial de asistencias de un miembro."""
    miembro_id = (request.GET.get("miembro_id") or "").strip()
    miembros = Miembro.objects.order_by("apellidos", "nombres")
    miembro = None
    asistencias = Asistencia.objects.none()
    if miembro_id:
        miembro = get_object_or_404(Miembro, pk=miembro_id)
        asistencias = Asistencia.objects.filter(miembro=miembro).select_related(
            "evento"
        ).order_by("-evento__fecha", "-evento__hora_inicio")
    return render(
        request,
        "eventos/asistencias_miembro.html",
        {
            "miembros": miembros,
            "miembro": miembro,
            "miembro_id": miembro_id,
            "asistencias": asistencias,
        },
    )


asistencia_consulta = asistencia_consulta_miembro
