from datetime import datetime
from django.db import models
from .cargo import Cargo
from .objetivo import Objetivo
    
class ObjetivoCargo(models.Model):
    objetivo = models.ForeignKey(Objetivo, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    fecha_asignacion = models.DateField(default=datetime.now, verbose_name='Fecha de Asignacion')
    activo = models.BooleanField(default=False, verbose_name='si esta activo')


    class Meta:        
        verbose_name = 'ObjetivoCargo'
        verbose_name_plural = 'ObjetivosCargos'
        db_table = 'objetivo_Cargo'
        ordering = ['id']  # - para oden descendente
        unique_together = ('objetivo', 'cargo')
        
    def __str__(self):
        return f"Objetivo {self.objetivo} - Cargo {self.cargo}"
