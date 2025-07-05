from django.db import models
from datetime import datetime

class Objetivo(models.Model):
    descripcion = models.CharField(max_length=255, verbose_name='Descripcion del objetivo')
    fecha_inicio = models.DateField(default=datetime.now, verbose_name='Fecha de inicio')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha de fin')
    estado = models.CharField(max_length=50, verbose_name='Estado del objetivo')

    class Meta:
        verbose_name = 'Objetivo'
        verbose_name_plural = 'Objetivos'
        db_table = 'objetivo'
        ordering = ['id']  # - para oden descendente

    def __str__(self):
        return self.descripcion
