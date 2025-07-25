from django.db import models
from .cargo import Cargo
from .departamento import Departamento

class CargoDepartamento(models.Model):
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    vacante = models.PositiveIntegerField(default=0, verbose_name='Cantidad Vacantes')
    visible = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.cargo} - {self.departamento}"
    
    class Meta:
        verbose_name = 'CargoDepartamento'
        verbose_name_plural = 'CargosDepartamentos'
        db_table = 'cargo_departamento'
        ordering = ['id']  # (-) para oden descendente

