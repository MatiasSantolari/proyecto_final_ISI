from django.db import models
from .tipo_criterio import TipoCriterio

class CriterioEvaluacion(models.Model):
    id_criterio = models.AutoField(primary_key=True, db_column="id_criterio")
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    ponderacion = models.DecimalField(max_digits=5, decimal_places=2)
    id_tipo_criterio = models.ForeignKey(TipoCriterio, on_delete=models.CASCADE, db_column="id_tipo_criterio")

    class Meta:
        db_table = "criterio_evaluacion"

    def __str__(self):
        return self.nombre
