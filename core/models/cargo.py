from django.db import models
from .departamento import Departamento


class Cargo(models.Model):
    nombre = models.CharField(max_length=50, verbose_name='Nombre Cargo')
    descripcion = models.CharField(max_length=255, verbose_name='Descripcion')

    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        db_table = 'cargo'
        ordering = ['id']  # (-) para oden descendente

    def __str__(self):
        return self.nombre