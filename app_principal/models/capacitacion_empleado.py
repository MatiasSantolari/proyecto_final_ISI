from django.db import models
from .capacitacion import Capacitacion
from .empleado import Empleado

class CapacitacionEmpleado(models.Model):
    id_capacitacion = models.ForeignKey(Capacitacion, on_delete=models.CASCADE, db_column="id_capacitacion")
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    fecha_inscripcion = models.DateField()
    estado = models.CharField(max_length=50)

    class Meta:
        db_table = "capacitacion_empleado"
        unique_together = ("id_capacitacion", "id_empleado")

    def __str__(self):
        return f"{self.id_empleado.persona.nombre} - {self.id_capacitacion.nombre}"