from django.db import models
from .empleado import Empleado
from .evaluacion import Evaluacion


class EvaluacionEmpleado(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="evaluaciones_recibidas")
    fecha_registro = models.DateField(verbose_name='Fecha de registro')
    comentarios = models.CharField(max_length=255, null=True, blank=True, verbose_name='Comentarios de la evaluacion')
    calificacion_final = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='Calificacion final de la evaluacion')


    class Meta:
        verbose_name = 'EvaluacionEmpleado'
        verbose_name_plural = 'EvaluacionesEmpleados'
        db_table = "evaluacion_empleado"
        ordering = ['id']
        unique_together = ('evaluacion', 'empleado')


    def __str__(self):
        return f"EvalEmp: {self.empleado} - {self.evaluacion}"
    

    def get_calificacion(self, criterio):
        calif = self.criterios_calificados.filter(criterio=criterio).first()
        return calif.calificacionCriterio if calif else ""