from django.db import models
from .competencia import Competencia
from .empleado import Empleado


class CompetenciaEmpleado(models.Model):
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'CompetenciaEmpleado'
        verbose_name_plural = 'CompetenciasEmpleados'
        db_table = "competencia_empleado"
        ordering = ['id']

    def __str__(self):
        return {self.empleado} + " - " + {self.competencia}
