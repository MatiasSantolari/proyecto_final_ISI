from django.db import models
from .empleado import Empleado

class HistorialAsistencia(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    fecha_asistencia = models.DateField()
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = 'historial_asistencia'
        unique_together = ('empleado', 'fecha_asistencia', 'hora_entrada')

    def __str__(self):
        return f"{self.empleado} - {self.fecha_asistencia} ({self.hora_entrada})"
