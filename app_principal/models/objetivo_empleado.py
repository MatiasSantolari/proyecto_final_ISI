from django.db import models
from .empleado import Empleado
from .objetivo import Objetivo

class ObjetivoEmpleado(models.Model):
    id_objetivo = models.ForeignKey(Objetivo, on_delete=models.CASCADE, db_column="id_objetivo")
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")

    class Meta:
        db_table = 'objetivos_empleado'  
        unique_together = ('id_objetivo', 'id_empleado')  

    def __str__(self):
        return f"Objetivo {self.id_objetivo_id} - Empleado {self.id_empleado_id}"
