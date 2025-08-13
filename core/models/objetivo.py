from django.db import models
from datetime import datetime
from .usuario import Usuario
from .departamento import Departamento

class Objetivo(models.Model):
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, null=True, blank=True)
    titulo = models.CharField(max_length=255, verbose_name='Titulo del objetivo')
    descripcion = models.CharField(max_length=255, null=True, blank=True, verbose_name='Descripcion del objetivo')
    creado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='objetivos_creados')
    fecha_creacion = models.DateField(default=datetime.now, verbose_name='Fecha de creacion')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha de fin')
    es_recurrente = models.BooleanField(default=False, verbose_name='si es recurrente')
    activo = models.BooleanField(default=True, verbose_name='estado de actividad')

    class Meta:
        verbose_name = 'Objetivo'
        verbose_name_plural = 'Objetivos'
        db_table = 'objetivo'
        ordering = ['id']  # - para oden descendente

    def __str__(self):
        return self.descripcion
