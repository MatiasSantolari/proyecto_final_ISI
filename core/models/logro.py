from datetime import datetime
from django.db import models

class Logro(models.Model):
    descripcion = models.CharField(max_length=255, verbose_name='Descripcion del logro')
    fecha_inicio = models.DateField(default=datetime.now, verbose_name='Fecha de inicio')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha de fin')


    class Meta:
        verbose_name = 'Logro'
        verbose_name_plural = 'Logros'
        db_table = 'logro'
        ordering = ['id']  # - para oden descendente

    def __str__(self):
        return self.descripcion
