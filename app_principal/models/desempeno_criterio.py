from django.db import models
from .criterio_evaluacion import CriterioEvaluacion
from .empleado import Empleado
def get_evaluacion():
    from .evaluacion import Evaluacion
    return Evaluacion

class DesempenoCriterio(models.Model):
    id_criterio = models.ForeignKey(CriterioEvaluacion, on_delete=models.CASCADE, db_column="id_criterio")
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    id_evaluacion = models.ForeignKey("app_principal.Evaluacion", on_delete=models.CASCADE, db_column="id_evaluacion")
    fecha_evaluacion = models.DateField()

    class Meta:
        db_table = "desempeno_criterio"
        unique_together = ("id_criterio", "id_empleado", "id_evaluacion", "fecha_evaluacion")

    def __str__(self):
        return f"Criterio {self.id_criterio} - Empleado {self.id_empleado} - Evaluacion {self.id_evaluacion} - {self.fecha_evaluacion}"
