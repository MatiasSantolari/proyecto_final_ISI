from django.db import models
from datetime import datetime
from .cargo import Cargo
from .empleado import Empleado

class EmpleadoCargo(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    fecha_inicio = models.DateField(default=datetime.now, verbose_name='Fecha de asignacion')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha de desasignacion')
    
    def __str__(self):
        return self.empleado + " - " + self.cargo

    class Meta:
        verbose_name = 'EmpleadoCargo'
        verbose_name_plural = 'EmpleadosCargos'
        db_table = 'empleado_cargo'
        ordering = ['id']  # - para oden descendente
    

    