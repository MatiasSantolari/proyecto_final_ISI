from django.db import models

class CargoDepartamento(models.Model):
    id_cargo = models.ForeignKey("app_principal.Cargo", on_delete=models.CASCADE, db_column="id_cargo")
    id_departamento = models.ForeignKey("app_principal.Departamento", on_delete=models.CASCADE, db_column="id_departamento")

    class Meta:
        db_table = "cargo_departamento"
        unique_together = ("id_cargo", "id_departamento")
