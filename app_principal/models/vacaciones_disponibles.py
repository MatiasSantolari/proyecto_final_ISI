from django.db import models
from .empleado import Empleado

class VacacionesDisponibles(models.Model):
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    fecha = models.DateField()
    cantidad_dias_disponibles = models.IntegerField()

    class Meta:
        db_table = "vacaciones_disponibles"
        unique_together = ("id_empleado", "fecha")
