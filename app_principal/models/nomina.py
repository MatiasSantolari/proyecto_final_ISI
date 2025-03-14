from django.db import models
from .empleado import Empleado
from .historial_sueldo_base import HistorialSueldoBase
from .nomina_historial_sueldo import NominaHistorialSueldo

class Nomina(models.Model):
    id_nomina = models.AutoField(primary_key=True)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_generacion = models.DateField()
    monto_bruto = models.DecimalField(max_digits=10, decimal_places=2)
    monto_neto = models.DecimalField(max_digits=10, decimal_places=2)
    cant_dias_trabajados = models.IntegerField()
    total_descuentos = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=50)
    periodo = models.CharField(max_length=50)

    historial_sueldos = models.ManyToManyField(HistorialSueldoBase, through=NominaHistorialSueldo, related_name="nominas")
    
    class Meta:
        db_table = "nomina"

    def __str__(self):
        return f"Nómina {self.id_nomina} - {self.empleado}"
