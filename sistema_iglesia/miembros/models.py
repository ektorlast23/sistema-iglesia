from django.db import models


class Familia(models.Model):
    nombre_familia = models.CharField(max_length=100, unique=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    fecha_registro = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "familias"
        verbose_name_plural = "familias"

    def __str__(self):
        return self.nombre_familia


class Ministerio(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "ministerios"

    def __str__(self):
        return self.nombre


class Miembro(models.Model):
    ESTADO_CHOICES = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
        ("visitante", "Visitante"),
    ]
    SEXO_CHOICES = [("M", "Masculino"), ("F", "Femenino")]

    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    familia = models.ForeignKey(Familia, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default="activo")
    ministerios = models.ManyToManyField(
        Ministerio, through="MiembroMinisterio", related_name="miembros"
    )

    class Meta:
        db_table = "miembros"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class MiembroMinisterio(models.Model):
    miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE)
    ministerio = models.ForeignKey(Ministerio, on_delete=models.CASCADE)
    fecha_asignacion = models.DateField(null=True, blank=True)
    rol = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "miembros_ministerios"
        unique_together = ("miembro", "ministerio")

    def __str__(self):
        return f"{self.miembro} en {self.ministerio}"
