from django.db import models
from .empleado import Empleado
from .descuento import Descuento
from .nomina import Nomina

class DescuentoEmpleadoNomina(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    descuento = models.ForeignKey(Descuento, on_delete=models.CASCADE)
    nomina = models.ForeignKey(Nomina, on_delete=models.CASCADE)

    class Meta:
        db_table = "descuento_empleado_nomina"
        unique_together = ("empleado", "descuento", "nomina")

    def __str__(self):
        return f"{self.empleado} - {self.descuento} - Nómina {self.nomina.id_nomina}"
