from django.db import models
from .tipo_criterio import TipoCriterio

class CriterioEvaluacion(models.Model):
    tipo_criterio = models.ForeignKey(TipoCriterio, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100, verbose_name='Nombre del criterio de evaluacion')
    descripcion = models.CharField(max_length=255, null=True, blank=True, verbose_name='Descripcion del criterio')
    ponderacion = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Ponderacion del criterio')

    class Meta:
        verbose_name = 'CriterioEvaluacion'
        verbose_name_plural = 'CriteriosEvaluacion'
        db_table = "criterio_evaluacion"

    def __str__(self):
        return self.nombre
