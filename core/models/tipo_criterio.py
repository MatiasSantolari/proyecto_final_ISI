from django.db import models


class TipoCriterio(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre del tipo de criterio')
    descripcion = models.CharField(max_length=255, null=True, blank=True, verbose_name='Descripcion del tipo de criterio')

    class Meta:
        verbose_name = 'TipoCriterio'
        verbose_name_plural = 'TiposCriterios'
        db_table = "tipo_criterio"
        ordering = ['id']

    def __str__(self):
        return self.nombre
