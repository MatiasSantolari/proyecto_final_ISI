from django.db import models
from .cargo import Cargo
from .departamento import Departamento

class CargoDepartamento(models.Model):
    id_cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, db_column="id_cargo")
    id_departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, db_column="id_departamento")

    class Meta:
        db_table = "cargo_departamento"
        unique_together = ("id_cargo", "id_departamento")
