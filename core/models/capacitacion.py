from django.db import models
from .institucion import Institucion

class Capacitacion(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la capacitacion')
    descripcion = models.CharField(max_length=255, null=True, blank=True, verbose_name='Descripcion de la capacitacion')
    fecha_inicio = models.DateField(verbose_name='Fecha de inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de fin')
    origen_org = models.BooleanField(default=False, verbose_name='Origen Capacitacion')
    presencial = models.BooleanField(default=True, verbose_name='Es presencial')
    cupo = models.PositiveIntegerField(default=0, verbose_name='Cantidad de cupos')
    

    class Meta:
        verbose_name = 'capacitacion'
        verbose_name_plural = 'Capacitaciones'
        db_table = "capacitacion"
        ordering = ['id']

    def __str__(self):
        return self.nombre
