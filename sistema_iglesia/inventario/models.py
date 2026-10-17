"""Modelos del modulo de inventario (Semana 6).

Equipo: catalogo de instrumentos, sonido, mobiliario y recursos.
Prestamo: salida temporal de equipos asociada a un miembro responsable.

La disponibilidad NO se almacena: se calcula restando los prestamos activos,
para evitar descuadres entre la cantidad total y lo que esta afuera.
"""

from django.db import models

from miembros.models import Miembro


class Equipo(models.Model):
    CATEGORIA_CHOICES = [
        ("instrumento", "Instrumento"),
        ("sonido", "Sonido"),
        ("mobiliario", "Mobiliario"),
        ("recurso", "Recurso"),
    ]
    ESTADO_CHOICES = [
        ("disponible", "Disponible"),
        ("mantenimiento", "En mantenimiento"),
        ("baja", "De baja"),
    ]

    nombre = models.CharField(max_length=150)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    descripcion = models.TextField(null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="disponible")
    ubicacion = models.CharField(max_length=150, null=True, blank=True)
    fecha_registro = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "equipos"
        ordering = ["categoria", "nombre"]
        verbose_name_plural = "equipos"

    def __str__(self):
        return self.nombre

    @property
    def cantidad_prestada(self):
        """Unidades actualmente en prestamos activos."""
        return (
            self.prestamos.filter(estado="prestado").aggregate(t=models.Sum("cantidad"))["t"]
            or 0
        )

    @property
    def cantidad_disponible(self):
        """Unidades que pueden prestarse en este momento."""
        if self.estado == "baja":
            return 0
        return max(self.cantidad - self.cantidad_prestada, 0)

    @property
    def disponible(self):
        return self.estado != "baja" and self.cantidad_disponible > 0


class Prestamo(models.Model):
    ESTADO_CHOICES = [
        ("prestado", "Prestado"),
        ("devuelto", "Devuelto"),
    ]

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="prestamos")
    miembro = models.ForeignKey(Miembro, on_delete=models.PROTECT, related_name="prestamos")
    cantidad = models.PositiveIntegerField(default=1)
    fecha_prestamo = models.DateField()
    fecha_devolucion_prevista = models.DateField()
    fecha_devolucion_real = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default="prestado")
    observaciones = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "prestamos"
        ordering = ["-fecha_prestamo", "-id"]

    def __str__(self):
        return f"{self.cantidad} x {self.equipo} -> {self.miembro}"

    @property
    def activo(self):
        return self.estado == "prestado"

    @property
    def atrasado(self):
        from django.utils import timezone

        return (
            self.estado == "prestado"
            and self.fecha_devolucion_prevista < timezone.localdate()
        )
