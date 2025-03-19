from django.db import models
from .historial_sueldo_base import HistorialSueldoBase

class NominaHistorialSueldo(models.Model):
    nomina = models.ForeignKey('app_principal.Nomina', on_delete=models.CASCADE)
    historial_sueldo = models.ForeignKey(HistorialSueldoBase, on_delete=models.CASCADE)

    class Meta:
        db_table = "nomina_historial_sueldo"
        unique_together = ("nomina", "historial_sueldo")

    def __str__(self):
        return f"Nómina {self.nomina.id_nomina} - Sueldo Base {self.historial_sueldo.sueldo_base}"

