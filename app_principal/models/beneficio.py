from django.db import models

class Beneficio(models.Model):
    id_beneficio = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "beneficio"

    def __str__(self):
        return f"{self.descripcion} - ${self.monto}"
