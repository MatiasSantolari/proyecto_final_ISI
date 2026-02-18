from datetime import datetime
from django.db import models


TIPO_LOGRO_CHOICES = [
    ('ASISTENCIA_PERFECTA', 'Asistencia Perfecta Mensual'),
    ('ANTIGUEDAD_1', 'Antiguedad de 1 año'),
    ('ANTIGUEDAD_3', 'Antiguedad de 3 años'),
    ('ANTIGUEDAD_5', 'Antiguedad de 5 años'),
    ('ANTIGUEDAD_10', 'Antiguedad de 10 años'),
    ('ANTIGUEDAD_15', 'Antiguedad de 15 años'),
    ('ANTIGUEDAD_20', 'Antiguedad de 20 años'),
    ('ANTIGUEDAD_25', 'Antiguedad de 25 años'),
    ('ANTIGUEDAD_30', 'Antiguedad de 30 años'),
    ('ANTIGUEDAD_40', 'Antiguedad de 40 años')
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
