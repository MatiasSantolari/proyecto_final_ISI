from django.db import models
from .criterio_evaluacion import CriterioEvaluacion
from .evaluacion import Evaluacion
from .empleado import Empleado

class DesempenoCriterio(models.Model):
    id_criterio = models.ForeignKey(CriterioEvaluacion, on_delete=models.CASCADE, db_column="id_criterio")
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    fecha_evaluacion = models.DateField()

    class Meta:
        db_table = "desempeno_criterio"
        unique_together = ("id_criterio", "id_empleado", "fecha_evaluacion")

    def __str__(self):
        return f"Criterio {self.id_criterio} - Empleado {self.id_empleado} - {self.fecha_evaluacion}"
