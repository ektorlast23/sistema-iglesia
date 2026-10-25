"""Formularios del modulo de eventos (Semana 7)."""

from django import forms

from miembros.models import Miembro

from .models import Asistencia, Evento


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            "nombre",
            "descripcion",
            "fecha",
            "hora_inicio",
            "hora_fin",
            "lugar",
            "tipo",
            "responsable",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "hora_fin": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "nombre": "Nombre del evento",
            "descripcion": "Descripción",
            "fecha": "Fecha",
            "hora_inicio": "Hora de inicio",
            "hora_fin": "Hora de fin",
            "lugar": "Lugar",
            "tipo": "Tipo",
            "responsable": "Responsable",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsable"].queryset = Miembro.objects.filter(
            estado="activo"
        ).order_by("apellidos", "nombres")

    def clean(self):
        cleaned = super().clean()
        hora_inicio = cleaned.get("hora_inicio")
        hora_fin = cleaned.get("hora_fin")
        if hora_inicio and hora_fin and hora_fin < hora_inicio:
            self.add_error(
                "hora_fin", "La hora de fin no puede ser anterior a la de inicio."
            )
        return cleaned


class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = ["miembro", "evento", "fecha", "estado", "observaciones"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "observaciones": forms.TextInput(attrs={"maxlength": 255}),
        }
        labels = {
            "miembro": "Miembro",
            "evento": "Evento",
            "fecha": "Fecha",
            "estado": "Estado",
            "observaciones": "Observaciones",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["miembro"].queryset = Miembro.objects.filter(
            estado="activo"
        ).order_by("apellidos", "nombres")
        self.fields["evento"].queryset = Evento.objects.order_by("-fecha")

    def clean(self):
        cleaned = super().clean()
        miembro = cleaned.get("miembro")
        evento = cleaned.get("evento")
        if self.instance.pk is None and miembro and evento:
            if Asistencia.objects.filter(miembro=miembro, evento=evento).exists():
                self.add_error(
                    "__all__",
                    "Ese miembro ya tiene asistencia registrada en este evento.",
                )
        return cleaned


class AsistenciaEditarForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = ["estado", "observaciones"]
        labels = {
            "estado": "Estado",
            "observaciones": "Observaciones",
        }
