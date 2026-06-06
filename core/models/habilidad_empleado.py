from django.db import models
from .habilidad import Habilidad
from .empleado import Empleado

class HabilidadEmpleado(models.Model):
    habilidad = models.ForeignKey(Habilidad, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_asignacion = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'HabilidadEmpleado'
        verbose_name_plural = 'HabilidadesEmpleados'
        db_table = 'habilidad_empleado'
        ordering = ['id']  # - para oden descendente
    
    def __str__(self):
        return f"{self.empleado} - {self.habilidad}"
