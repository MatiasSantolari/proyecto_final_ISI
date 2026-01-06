from django.db import models
from .logro import Logro
from .empleado import Empleado

class LogroEmpleado(models.Model):
    logro = models.ForeignKey(Logro, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    completado = models.BooleanField(default=False, verbose_name='estado de completitud')
    fecha_asignacion = models.DateField(null=True, blank=True, verbose_name='Fecha de completado')

    class Meta:
        verbose_name = 'LogroEmpleado'
        verbose_name_plural = 'LogrosEmpleados'
        db_table = 'logro_empleado'
        ordering = ['id']  # - para oden descendente

    
    def __str__(self):
        return f"Logro {self.logro} - Empleado {self.empleado}"
