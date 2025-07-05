from django.db import models
from .capacitacion import Capacitacion
from .empleado import Empleado


class CapacitacionEmpleado(models.Model):
    capacitacion = models.ForeignKey(Capacitacion, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_inscripcion = models.DateField(verbose_name='Fecha de inscripcion')
    estado = models.CharField(max_length=50, verbose_name='Estado de la Capacitacion')

    class Meta:
        verbose_name = "CapacitacionEmpleado"
        verbose_name_plural = "CapacitacionesEmpleados"
        db_table = "capacitacion_empleado"
        ordering = ['id']
