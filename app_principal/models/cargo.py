from django.db import models
from .departamento import Departamento
from .cargo_departamento import CargoDepartamento

class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, null=False)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    total_vacantes = models.IntegerField(null=False)

    departamentos = models.ManyToManyField(Departamento, through=CargoDepartamento, related_name="cargos")
    
    class Meta:
        db_table = "cargo"

    def __str__(self):
        return self.nombre
