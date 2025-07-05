from datetime import datetime
from django.db import models
from .cargo import Cargo

class HistorialSueldoBase(models.Model):
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    fecha_sueldo = models.DateTimeField(default=datetime.now, verbose_name='Fecha carga nuevo sueldo')
    sueldo_base = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Sueldo Base')

    class Meta:
        verbose_name = 'HistorialSueldoBase'
        verbose_name_plural = 'HistorialSueldosBase'
        db_table = "historial_sueldo_base"
        ordering = ['id']

    def __str__(self):
        return f"{self.cargo.nombre} - {self.fecha_sueldo} - ${self.sueldo_base}"
