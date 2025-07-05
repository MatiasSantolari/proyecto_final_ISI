from datetime import datetime
from django.db import models
from .empleado import Empleado

class VacacionesSolicitud(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_solicitud = models.DateField(default=datetime.now, verbose_name='Fecha de solicitud')
    fecha_inicio_estimada = models.DateField(verbose_name='Fecha comienzo vacaciones')
    cant_dias_solicitados = models.PositiveIntegerField(verbose_name='Cantidad dias de vacaciones solicitados')
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, verbose_name='Estado de la solicitud de vacaciones')

    class Meta:
        verbose_name = "VacacionesSolicitud"
        verbose_name_plural = "VacacionesSolicitudes"
        db_table = "vacaciones_solicitud"
        ordering = ['id']