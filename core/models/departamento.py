from django.db import models


class Departamento(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        db_table = 'departamento'
        ordering = ['id']  # (-) para oden descendente

    def __str__(self):
        return self.nombre
