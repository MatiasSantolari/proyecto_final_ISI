from django.db import models
from .objetivo import Objetivo
from .empleado import Empleado
from .cargo import Cargo
    
class ObjetivoEmpleado(models.Model):
    objetivo = models.ForeignKey(Objetivo, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    fecha_creacion = models.DateField(auto_now_add=True, verbose_name='Fecha de Creacion')
    fecha_completado = models.DateField(null=True, blank=True, verbose_name='Fecha de Completitud')

    class Meta:        
        verbose_name = 'ObjetivoEmpleado'
        verbose_name_plural = 'ObjetivosEmpleados'
        db_table = 'objetivo_empleado'
        ordering = ['id']  # - para oden descendente
        unique_together = ('objetivo', 'empleado', 'cargo')
        
    def __str__(self):
        return f"Objetivo {self.objetivo} - Empleado {self.empleado}"
