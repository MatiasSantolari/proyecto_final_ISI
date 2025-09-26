from django.db import models
from .criterio import Criterio
from .evaluacion_empleado import EvaluacionEmpleado

class EvaluacionEmpleadoCriterio(models.Model):
    evaluacion_empleado = models.ForeignKey(EvaluacionEmpleado, on_delete=models.CASCADE)
    criterio = models.ForeignKey(Criterio, on_delete=models.CASCADE)
    calificacion_criterio = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='Calificacion del criterio')


    class Meta:
        verbose_name = 'EvaluacionEmpleadoCriterio'
        verbose_name_plural = 'EvaluacionesEmpleadosCriterios'
        db_table = "evaluacion_empleado_criterio"
        ordering = ['id']
        unique_together = ('evaluacion_empleado', 'criterio')


    def __str__(self):
        return f"{self.evaluacion_empleado} - {self.criterio}: {self.calificacion_criterio}"
