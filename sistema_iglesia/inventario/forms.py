"""Formularios del modulo de inventario (Semana 6).

EquipoForm: alta y edicion del catalogo de equipos.
PrestamoForm: registro de prestamos con validacion de existencias.
"""

from django import forms

from .models import Equipo, Prestamo


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ["nombre", "categoria", "descripcion", "cantidad", "estado", "ubicacion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"maxlength": 150}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "cantidad": forms.NumberInput(attrs={"min": 1}),
            "ubicacion": forms.TextInput(attrs={"maxlength": 150}),
        }
        labels = {
            "nombre": "Nombre del equipo",
            "categoria": "Categoría",
            "descripcion": "Descripción",
            "cantidad": "Cantidad total",
            "estado": "Estado",
            "ubicacion": "Ubicación",
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get("cantidad")
        if cantidad is None or cantidad < 1:
            raise forms.ValidationError("La cantidad debe ser al menos 1.")
        return cantidad


class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = [
            "equipo",
            "miembro",
            "cantidad",
            "fecha_prestamo",
            "fecha_devolucion_prevista",
            "observaciones",
        ]
        widgets = {
            "fecha_prestamo": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "fecha_devolucion_prevista": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "cantidad": forms.NumberInput(attrs={"min": 1}),
            "observaciones": forms.TextInput(attrs={"maxlength": 255}),
        }
        labels = {
            "equipo": "Equipo",
            "miembro": "Miembro responsable",
            "cantidad": "Cantidad a prestar",
            "fecha_prestamo": "Fecha de préstamo",
            "fecha_devolucion_prevista": "Fecha prevista de devolución",
            "observaciones": "Observaciones",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo equipos que pueden prestarse en este momento.
        self.fields["equipo"].queryset = Equipo.objects.exclude(estado="baja")

    def clean(self):
        cleaned = super().clean()
        equipo = cleaned.get("equipo")
        cantidad = cleaned.get("cantidad")
        f_inicio = cleaned.get("fecha_prestamo")
        f_fin = cleaned.get("fecha_devolucion_prevista")

        if equipo and cantidad is not None:
            if cantidad < 1:
                self.add_error("cantidad", "La cantidad debe ser al menos 1.")
            elif cantidad > equipo.cantidad_disponible:
                self.add_error(
                    "cantidad",
                    f"Solo hay {equipo.cantidad_disponible} unidad(es) disponible(s) "
                    f"de {equipo.nombre}.",
                )
        if f_inicio and f_fin and f_fin < f_inicio:
            self.add_error(
                "fecha_devolucion_prevista",
                "La fecha de devolución no puede ser anterior a la del préstamo.",
            )
        return cleaned
