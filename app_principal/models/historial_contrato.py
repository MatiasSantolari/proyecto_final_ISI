from django.db import models
from .empleado import Empleado
from .tipo_contrato import TipoContrato

class HistorialContrato(models.Model):
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    id_contrato = models.ForeignKey(TipoContrato, on_delete=models.CASCADE, db_column="id_contrato")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    condiciones = models.CharField(max_length=255)

    class Meta:
        db_table = 'historial_contrato'
        unique_together = ('id_empleado', 'fecha_inicio')

    def __str__(self):
        return f"Contrato de {self.id_empleado} ({self.fecha_inicio} - {self.fecha_fin})"
