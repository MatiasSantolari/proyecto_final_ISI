from django.db import models
from .tipo_contrato import TipoContrato
from .empleado import Empleado
from .cargo import Cargo

class HistorialContrato(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    contrato = models.ForeignKey(TipoContrato, on_delete=models.SET_NULL, null=True, blank=True)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Fecha inicio')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha fin')
    condiciones = models.CharField(max_length=255, null=True, blank=True, verbose_name='Condiciones del contrato')
    monto_extra_pactado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Sueldo pactado")
    estado = models.CharField(
        max_length=20,
        choices=[("activo", "Activo"), ("finalizado", "Finalizado"), ("renovado", "Renovado")],
        default="activo",
        verbose_name="Estado del contrato"
    )

    class Meta:
        verbose_name = 'HistorialContrato'
        verbose_name_plural = 'HistorialContratos'
        db_table = 'historial_contrato'
    
    def __str__(self):
        return f"{self.empleado} - {self.contrato} ({self.fecha_inicio} - {self.fecha_fin})"