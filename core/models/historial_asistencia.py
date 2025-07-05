from datetime import datetime
from django.db import models
from .empleado import Empleado

class HistorialAsistencia(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_asistencia = models.DateField(default=datetime.now, verbose_name='Fecha de ingreso')
    hora_entrada = models.TimeField(default=datetime.now, verbose_name='Hora de ingreso')
    hora_salida = models.TimeField(null=True, blank=True, verbose_name='Hora de salida')

    class Meta:
        verbose_name='HistorialAsistencia'
        verbose_name_plural='HistorialAsistencias'
        db_table = 'historial_asistencia'
        ordering = ['id']

    def __str__(self):
        return f"{self.empleado} - {self.fecha_asistencia} ({self.hora_entrada})"
