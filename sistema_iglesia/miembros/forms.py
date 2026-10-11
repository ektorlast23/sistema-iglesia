"""Formularios del modulo de miembros (Semana 5).

El telefono se guarda como texto para conservar prefijos y ceros iniciales.
"""

from django import forms

from .models import Miembro


class MiembroForm(forms.ModelForm):
    """Alta y edicion de miembros: 8 campos + familia (select)."""

    class Meta:
        model = Miembro
        fields = [
            "nombres",
            "apellidos",
            "fecha_nacimiento",
            "telefono",
            "email",
            "direccion",
            "fecha_ingreso",
            "estado",
            "familia",
        ]
        widgets = {
            "nombres": forms.TextInput(attrs={"maxlength": 100}),
            "apellidos": forms.TextInput(attrs={"maxlength": 100}),
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "telefono": forms.TextInput(attrs={"maxlength": 20, "placeholder": "0000-0000"}),
            "email": forms.EmailInput(attrs={"maxlength": 100}),
            "direccion": forms.TextInput(attrs={"maxlength": 255}),
            "fecha_ingreso": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }
        labels = {
            "nombres": "Nombres",
            "apellidos": "Apellidos",
            "fecha_nacimiento": "Fecha de nacimiento",
            "telefono": "Teléfono",
            "email": "Correo electrónico",
            "direccion": "Dirección",
            "fecha_ingreso": "Fecha de registro",
            "estado": "Estado",
            "familia": "Familia",
        }

    def clean_telefono(self):
        """El telefono es texto: se acepta vacio o cualquier combinacion valida."""
        telefono = (self.cleaned_data.get("telefono") or "").strip()
        if telefono and len(telefono) > 20:
            raise forms.ValidationError("El teléfono no puede superar 20 caracteres.")
        return telefono or None
