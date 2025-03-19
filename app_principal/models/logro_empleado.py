from django.db import models
from .logro import Logro
from django.apps import apps

class LogroEmpleado(models.Model):
    id_logro = models.ForeignKey(Logro, on_delete=models.CASCADE, db_column="id_logros")
    id_empleado = models.ForeignKey("app_principal.Empleado", on_delete=models.CASCADE, db_column="id_empleado")

    class Meta:
        db_table = 'logros_empleado'
        unique_together = ('id_logro', 'id_empleado')

    def get_empleado(self):
        Empleado = apps.get_model('app_principal', 'Empleado')
        return Empleado.objects.get(id=self.id_empleado)
    
    def __str__(self):
        return f"Logro {self.id_logro_id} - Empleado {self.id_empleado_id}"
