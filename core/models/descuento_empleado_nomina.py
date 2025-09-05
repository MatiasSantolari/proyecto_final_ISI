from django.db import models
from .descuento import Descuento
from .nomina import Nomina
from .empleado import Empleado

class DescuentoEmpleadoNomina(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    descuento = models.ForeignKey(Descuento, on_delete=models.CASCADE)
    nomina = models.ForeignKey(Nomina, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = 'DescuentoEmpleadoNomina'
        verbose_name_plural = 'DescuentosEmpleadosNominas'
        db_table = "descuento_empleado_nomina"
        ordering = ['id']

    def __str__(self):
        return f"{self.empleado} - {self.descuento} - Nómina {self.nomina}"
