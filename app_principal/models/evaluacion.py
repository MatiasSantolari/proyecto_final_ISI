from django.db import models
from .empleado import Empleado
from .criterio_evaluacion import CriterioEvaluacion
from .desempeno_criterio import DesempenoCriterio

class Evaluacion(models.Model):
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    fecha_evaluacion = models.DateField()
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    comentarios = models.CharField(max_length=255, null=True, blank=True)
    calificacion_final = models.DecimalField(max_digits=5, decimal_places=2)

    criterios = models.ManyToManyField(CriterioEvaluacion,through=DesempenoCriterio,related_name="evaluaciones")

    class Meta:
        db_table = "evaluacion"
        unique_together = ("id_empleado", "fecha_evaluacion")

    def __str__(self):
        return f"Evaluación {self.fecha_evaluacion} - {self.id_empleado}"
