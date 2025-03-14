from django.db import models
from .empleado import Empleado
from .cargo import Cargo

class EmpleadoCargo(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    fecha_asignacion = models.DateField()
    fecha_desasignado = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "empleado_cargo"
        unique_together = ("empleado", "cargo", "fecha_asignacion")

    def __str__(self):
        return f"{self.empleado} - {self.cargo} ({self.fecha_asignacion})"
