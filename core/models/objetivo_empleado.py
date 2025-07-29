from datetime import datetime
from django.db import models
from .objetivo import Objetivo
from .empleado import Empleado
    
class ObjetivoEmpleado(models.Model):
    objetivo = models.ForeignKey(Objetivo, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_asignacion = models.DateField(default=datetime.now, verbose_name='Fecha de Asignacion')
    fecha_limite = models.DateField(null=True, blank=True, verbose_name='Fecha limite')
    ESTADO_CHOICES = [
        ('en proceso', 'En Proceso'),
        ('completado', 'Completado'),
    ]
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='en proceso', verbose_name='Estado')


    class Meta:        
        verbose_name = 'ObjetivoEmpleado'
        verbose_name_plural = 'ObjetivosEmpleados'
        db_table = 'objetivo_empleado'
        ordering = ['id']  # - para oden descendente
        unique_together = ('objetivo', 'empleado')
        
    def __str__(self):
        return f"Objetivo {self.objetivo} - Empleado {self.empleado}"
