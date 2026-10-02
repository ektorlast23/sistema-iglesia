from django.db import models

from miembros.models import Miembro


class Evento(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(null=True, blank=True)
    fecha = models.DateField()
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    lugar = models.CharField(max_length=150, null=True, blank=True)
    tipo = models.CharField(max_length=50, null=True, blank=True)
    responsable = models.ForeignKey(
        Miembro, on_delete=models.SET_NULL, null=True, blank=True, related_name="eventos_responsable"
    )

    class Meta:
        db_table = "eventos"

    def __str__(self):
        return f"{self.nombre} ({self.fecha})"


class Asistencia(models.Model):
    miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE, related_name="asistencias")
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="asistencias")
    fecha = models.DateField()
    presente = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "asistencias"
        unique_together = ("miembro", "evento")

    def __str__(self):
        return f"{self.miembro} en {self.evento}: {'presente' if self.presente else 'ausente'}"
