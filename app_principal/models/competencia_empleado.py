from django.db import models
from .competencia import Competencia
from django.apps import apps


class CompetenciaEmpleado(models.Model):
    id_competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE, db_column="id_competencia")
    id_empleado = models.ForeignKey('app_principal.Empleado', on_delete=models.CASCADE, db_column="id_empleado")

    class Meta:
        db_table = "competencia_empleado"
        unique_together = ("id_competencia", "id_empleado")

    def get_empleado(self):
        Empleado = apps.get_model('app_principal', 'Empleado')
        return Empleado.objects.get(id=self.id_empleado_id)
    
    def __str__(self):
        return f"{self.id_empleado.persona.nombre} - {self.id_competencia.descripcion}"
