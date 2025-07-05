from django.db import models
from .tipo_contrato import TipoContrato
from .empleado import Empleado

class HistorialContrato(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    contrato = models.ForeignKey(TipoContrato, on_delete=models.CASCADE)
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Fecha inicio contrato')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha fin contrato')
    condiciones = models.CharField(max_length=255, verbose_name='Condiciones del contrato')

    class Meta:
        verbose_name = 'HistorialContrato'
        verbose_name_plural = 'HistorialContratos'
        db_table = 'historial_contrato'

    def __str__(self):
        return f"Contrato de {self.empleado} ({self.fecha_inicio} - {self.fecha_fin})"
