from django.db import models
from .empleado import Empleado
from .criterio_evaluacion import CriterioEvaluacion


class Evaluacion(models.Model):
    criterio = models.ManyToManyField(CriterioEvaluacion)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_evaluacion = models.DateField(verbose_name='Fecha de evaluacion')
    descripcion = models.CharField(max_length=255, null=True, blank=True, verbose_name='Descripcion de la evaluacion')
    comentarios = models.CharField(max_length=255, null=True, blank=True, verbose_name='Comentarios de la evaluacion')
    calificacion_final = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Calificacion final de la evaluacion')

    class Meta:
        verbose_name = 'Evaluacion'
        verbose_name_plural = 'Evaluaciones'
        db_table = "evaluacion"
        ordering = ['id']

    def __str__(self):
        return f"Evaluación {self.fecha_evaluacion} - {self.empleado}"
