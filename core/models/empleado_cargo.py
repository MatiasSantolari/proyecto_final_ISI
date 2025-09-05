from django.db import models
from datetime import datetime
from .cargo import Cargo
from .empleado import Empleado

class EmpleadoCargo(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_inicio = models.DateField(default=datetime.now, verbose_name='Fecha de asignacion')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha de desasignacion')
    

    class Meta:
        verbose_name = 'EmpleadoCargo'
        verbose_name_plural = 'EmpleadosCargos'
        db_table = 'empleado_cargo'
        ordering = ['id']  # - para oden descendente
    

    def __str__(self):
        return f"{self.empleado} - {self.cargo}"
