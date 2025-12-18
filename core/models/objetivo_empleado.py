from datetime import datetime
from django.db import models
from .objetivo import Objetivo
from .empleado import Empleado
from .cargo import Cargo
    
class ObjetivoEmpleado(models.Model):
    objetivo = models.ForeignKey(Objetivo, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_asignacion = models.DateField(default=datetime.now, verbose_name='Fecha de Asignacion')
    fecha_limite = models.DateField(null=True, blank=True, verbose_name='Fecha limite')
    completado = models.BooleanField(default=False, verbose_name='estado de completitud')

    class Meta:        
        verbose_name = 'ObjetivoEmpleado'
        verbose_name_plural = 'ObjetivosEmpleados'
        db_table = 'objetivo_empleado'
        ordering = ['id']  # - para oden descendente
        unique_together = ('objetivo', 'empleado', 'fecha_asignacion')
        
    def __str__(self):
        origen = f"Cargo: {self.cargo}" if self.cargo else "Asignación Manual"
        return f"{self.objetivo.titulo} - {self.empleado} ({origen})"
