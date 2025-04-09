from django.apps import apps
from django.db import models

class Departamento(models.Model):
    id_departamento = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    def get_cargo(self):
        Cargo = apps.get_model('app_principal', 'Cargo')
        return Cargo.objects.filter(departamento=self)
    
    cargos = models.ManyToManyField(
        "app_principal.Cargo",
        through="app_principal.CargoDepartamento",
         related_name="departamento_cargos"
    )
    
    class Meta:
        db_table = "departamento"

    def __str__(self):
        return self.nombre