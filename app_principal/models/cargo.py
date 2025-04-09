from django.db import models

class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, null=False)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    departamentos = models.ManyToManyField(
        "app_principal.Departamento",
        through="app_principal.CargoDepartamento",
        related_name="cargos_departamento"
    )
    
    class Meta:
        db_table = "cargo"

    def __str__(self):
        return self.nombre
