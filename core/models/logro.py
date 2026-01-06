from datetime import datetime
from django.db import models


TIPO_LOGRO_CHOICES = [
    ('ASISTENCIA_PERFECTA', 'Asistencia Perfecta Mensual')
]

class Logro(models.Model):
    descripcion = models.CharField(max_length=255, verbose_name='Descripcion del logro')
    fecha_creacion = models.DateField(default=datetime.now, verbose_name='Fecha de creacion')
    tipo = models.CharField(max_length=50, choices=TIPO_LOGRO_CHOICES, null=True, blank=True)


    class Meta:
        verbose_name = 'Logro'
        verbose_name_plural = 'Logros'
        db_table = 'logro'
        ordering = ['id']  # - para oden descendente

    def __str__(self):
        return self.descripcion
