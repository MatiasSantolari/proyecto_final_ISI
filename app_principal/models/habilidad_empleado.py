from django.db import models
from .habilidad import Habilidad
from .empleado import Empleado

class HabilidadEmpleado(models.Model):
    id_habilidad = models.ForeignKey(Habilidad, on_delete=models.CASCADE, db_column="id_habilidad")
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")

class Meta:
    db_table = "habilidad_empleado"
    unique_together = ("id_habilidad", "id_empleado")


def __str__(self):
    return f"{self.empleado.persona.nombre} - {self.habilidad.nombre}"
