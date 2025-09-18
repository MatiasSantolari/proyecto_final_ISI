from django.db import models
from .empleado import Empleado
from .evaluacion import Evaluacion


class EvaluacionEmpleado(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    evaluador = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_registro = models.DateField(verbose_name='Fecha de registro')
    comentarios = models.CharField(max_length=255, null=True, blank=True, verbose_name='Comentarios de la evaluacion')
    calificacion_final = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Calificacion final de la evaluacion')

    class Meta:
        verbose_name = 'EvaluacionEmpleado'
        verbose_name_plural = 'EvaluacionesEmpleados'
        db_table = "evaluacion_empleado"
        ordering = ['id']

    def __str__(self):
        return f"EvaluaciónEmpleado {self.fecha_registro}"
