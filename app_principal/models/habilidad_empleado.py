from django.db import models
from .habilidad import Habilidad
from django.apps import apps


class HabilidadEmpleado(models.Model):
    id_habilidad = models.ForeignKey(Habilidad, on_delete=models.CASCADE, db_column="id_habilidad")
    id_empleado = models.ForeignKey("app_principal.Empleado", on_delete=models.CASCADE, db_column="id_empleado")

    class Meta:
        db_table = "habilidad_empleado"
        unique_together = ("id_habilidad", "id_empleado")

    def get_empleado(self):
        Empleado = apps.get_model('app_principal', 'Empleado')
        return Empleado.objects.get(id=self.id_empleado)

    def __str__(self):
        return f"{self.empleado.persona.nombre} - {self.habilidad.nombre}"
