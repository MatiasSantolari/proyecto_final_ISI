from datetime import date
from django.db import models
from .empleado import Empleado

class VacacionesSolicitud(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_solicitud = models.DateField(default=date.today, verbose_name='Fecha de solicitud')
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Fecha de inicio')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha de fin')
    cant_dias_solicitados = models.PositiveIntegerField(verbose_name='Cantidad dias solicitados')

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    class Meta:
        verbose_name = "VacacionesSolicitud"
        verbose_name_plural = "VacacionesSolicitudes"
        db_table = "vacaciones_solicitud"
        ordering = ['id']

    def __str__(self):
        return f"{self.empleado} - {self.fecha_inicio} a {self.fecha_fin} ({self.estado})"