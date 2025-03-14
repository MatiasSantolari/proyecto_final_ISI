from django.db import models
from .competencia import Competencia
from .empleado import Empleado

class CompetenciaEmpleado(models.Model):
    id_competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE, db_column="id_competencia")
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")

    class Meta:
        db_table = "competencia_empleado"
        unique_together = ("id_competencia", "id_empleado")

    def __str__(self):
        return f"{self.id_empleado.persona.nombre} - {self.id_competencia.descripcion}"
