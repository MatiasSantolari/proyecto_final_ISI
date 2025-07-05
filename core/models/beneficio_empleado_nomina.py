from django.db import models
from .beneficio import Beneficio
from .nomina import Nomina
from .empleado import Empleado

class BeneficioEmpleadoNomina(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    beneficio = models.ForeignKey(Beneficio, on_delete=models.CASCADE)
    nomina = models.ForeignKey(Nomina, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'BeneficioEmpleadoNomina'
        verbose_name_plural = 'BeneficiosEmpleadosNominas'
        db_table = "beneficio_empleado_nomina"

    def __str__(self):
        return f"{self.empleado} - {self.beneficio} - Nómina {self.nomina}"
