from django.db import models
from .cargo import Cargo

class HistorialSueldoBase(models.Model):
    fecha_sueldo = models.DateTimeField()
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name='historial_sueldos')
    sueldo_base = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "historial_sueldo_base"
        unique_together = ("fecha_sueldo", "cargo")

    def __str__(self):
        return f"{self.cargo.nombre} - {self.fecha_sueldo} - ${self.sueldo_base}"
