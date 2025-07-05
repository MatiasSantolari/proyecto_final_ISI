from django.db import models
from .empleado import Empleado

class VacacionesDisponibles(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    cantidad_dias_disponibles = models.IntegerField()

    class Meta:
        verbose_name = 'vacacionesDisponibles'
        db_table = "vacaciones_disponibles"
        ordering = ['id']
