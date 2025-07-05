from datetime import datetime
from django.db import models
from .historial_sueldo_base import HistorialSueldoBase
from .empleado import Empleado

class Nomina(models.Model):
    historial_sueldos = models.ManyToManyField(HistorialSueldoBase)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_generacion = models.DateField(default=datetime.now, verbose_name='Fecha generacion nomina')
    monto_bruto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto bruto nomina')
    monto_neto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto Neto')
    cant_dias_trabajados = models.PositiveIntegerField(verbose_name='Cantidad de dias trabajados')
    total_descuentos = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total descuentos')
    estado = models.CharField(max_length=50, verbose_name='Estado de la nomina')
    periodo = models.CharField(max_length=50, verbose_name='Periodo perteneciente a la nomina')

    
    class Meta:
        verbose_name = 'Nomina'
        verbose_name_plural = 'Nominas'
        db_table = "nomina"
        ordering = ['id']

    def __str__(self):
        return f"Nómina {self.historial_sueldos} - {self.empleado}"
