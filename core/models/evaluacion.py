from django.db import models


class Evaluacion(models.Model):
    fecha_evaluacion = models.DateField(verbose_name='Fecha de evaluacion')
    descripcion = models.CharField(max_length=255, null=True, blank=True, verbose_name='Descripcion de la evaluacion')
   
    class Meta:
        verbose_name = 'Evaluacion'
        verbose_name_plural = 'Evaluaciones'
        db_table = "evaluacion"
        ordering = ['id']

    def __str__(self):
        return f"Evaluación {self.fecha_evaluacion}"
