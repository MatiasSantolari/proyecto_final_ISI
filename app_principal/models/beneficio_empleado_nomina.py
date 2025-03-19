from django.db import models
from .beneficio import Beneficio
from .nomina import Nomina

class BeneficioEmpleadoNomina(models.Model):
    empleado = models.ForeignKey('app_principal.Empleado', on_delete=models.CASCADE)
    beneficio = models.ForeignKey(Beneficio, on_delete=models.CASCADE)
    nomina = models.ForeignKey(Nomina, on_delete=models.CASCADE)

    class Meta:
        db_table = "beneficio_empleado_nomina"
        unique_together = ("empleado", "beneficio", "nomina")

    def __str__(self):
        return f"{self.empleado} - {self.beneficio} - Nómina {self.nomina.id_nomina}"
