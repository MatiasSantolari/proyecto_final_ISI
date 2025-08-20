from datetime import datetime
from django.db import models
from .historial_sueldo_base import HistorialSueldoBase
from .empleado import Empleado

class Nomina(models.Model):
    historial_sueldos = models.ManyToManyField(HistorialSueldoBase)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    numero = models.IntegerField(default=10, verbose_name='Numero de Nomina') # [id_empleado(6)-mes(2)-año(2)], Ejemplo: 0000010125 o 000001-01-25
    fecha_generacion = models.DateField(default=datetime.now, verbose_name='Fecha generacion nomina')
    monto_bruto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto bruto nomina')
    monto_neto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto Neto')
    cant_dias_trabajados = models.PositiveIntegerField(verbose_name='Cantidad de dias trabajados')
    total_descuentos = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total descuentos')
    ESTADO_CHOICES={
        ('pendiente', 'Pendiente'),
        ('generado', 'Generado'),
        ('pagado', 'Pagado'),
        ('Revisado', 'Revisado'),
        ('Anulado', 'Anulado')
    }
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, verbose_name='Estado de la nomina')
   
    
    class Meta:
        verbose_name = 'Nomina'
        verbose_name_plural = 'Nominas'
        db_table = "nomina"
        ordering = ['id']

    def __str__(self):
        return f"Nómina {self.historial_sueldos} - {self.empleado}"
