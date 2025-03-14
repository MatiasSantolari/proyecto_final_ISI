from django.db import models
from .cargo import Cargo
from .cargo_departamento import CargoDepartamento

class Departamento(models.Model):
    id_departamento = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    cargos = models.ManyToManyField(Cargo, through=CargoDepartamento, related_name="departamentos")

    class Meta:
        db_table = "departamento"
