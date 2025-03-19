from django.db import models
from .objetivo import Objetivo
from django.apps import apps

class ObjetivoEmpleado(models.Model):
    id_objetivo = models.ForeignKey(Objetivo, on_delete=models.CASCADE, db_column="id_objetivo")
    id_empleado = models.ForeignKey("app_principal.Empleado", on_delete=models.CASCADE, db_column="id_empleado")

    class Meta:
        db_table = 'objetivos_empleado'  
        unique_together = ('id_objetivo', 'id_empleado')  

    def get_empleado(self):
        Empleado = apps.get_model('app_principal', 'Empleado')
        return Empleado.objects.get(id=self.id_empleado)

    def __str__(self):
        return f"Objetivo {self.id_objetivo_id} - Empleado {self.id_empleado_id}"
