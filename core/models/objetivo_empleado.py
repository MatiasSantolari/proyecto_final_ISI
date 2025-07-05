from django.db import models
from .objetivo import Objetivo
from .empleado import Empleado

class ObjetivoEmpleado(models.Model):
    objetivo = models.ForeignKey(Objetivo, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)

    class Meta:        
        verbose_name = 'ObjetivoEmpleado'
        verbose_name_plural = 'ObjetivosEmpleados'
        db_table = 'objetivo_empleado'
        ordering = ['id']  # - para oden descendente

    def __str__(self):
        return f"Objetivo {self.objetivo} - Empleado {self.empleado}"
