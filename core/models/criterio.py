from django.db import models
from .tipo_criterio import TipoCriterio

class Criterio(models.Model):
    tipo_criterio = models.ForeignKey(TipoCriterio, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255, null=True, blank=True, verbose_name='Descripcion del criterio')
    
    class Meta:
        verbose_name = 'Criterio'
        verbose_name_plural = 'Criterios'
        db_table = "criterio"

    def __str__(self):
        return self.descripcion
