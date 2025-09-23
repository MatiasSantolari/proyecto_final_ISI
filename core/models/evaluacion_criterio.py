from django.db import models
from .criterio import Criterio
from .evaluacion import Evaluacion


class EvaluacionCriterio(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE)
    criterio = models.ForeignKey(Criterio, on_delete=models.CASCADE)
    ponderacion = models.DecimalField(max_digits=6, decimal_places=4, verbose_name='Ponderacion del criterio')


    class Meta:
        verbose_name = 'EvaluacionCriterio'
        verbose_name_plural = 'EvaluacionesCriterios'
        db_table = "evaluacion_criterio"
        ordering = ['id']
        unique_together = ('evaluacion', 'criterio')


    def __str__(self):
        return f"{self.evaluacion} - {self.criterio} ({self.ponderacion})"
