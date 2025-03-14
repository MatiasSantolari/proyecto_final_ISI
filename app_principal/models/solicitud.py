from django.db import models
from .persona import Persona
from .cargo import Cargo

class Solicitud(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    id_solicitud = models.AutoField(primary_key=True)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, db_column="id_persona")
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, db_column="id_cargo")
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    fecha_postulacion = models.DateField(null=False)
    estado_postulacion = models.CharField(max_length=10, choices=ESTADO_CHOICES, null=False)

    class Meta:
        db_table = "solicitud"

    def __str__(self):
        return f"{self.persona} - {self.cargo} ({self.estado_postulacion})"
