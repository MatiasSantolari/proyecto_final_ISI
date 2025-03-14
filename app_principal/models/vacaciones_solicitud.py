from django.db import models
from .empleado import Empleado

class VacacionesSolicitud(models.Model):
    id_solicitud = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    fecha_solicitud = models.DateField()
    fecha_inicio_estimada = models.DateField()
    fecha_fin_estimada = models.DateField()
    cant_dias_solicitados = models.IntegerField()

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)

    class Meta:
        db_table = "vacaciones_solicitud"
