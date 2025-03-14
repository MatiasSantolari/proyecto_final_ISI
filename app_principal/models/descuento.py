from django.db import models

class Descuento(models.Model):
    id_descuento = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "descuento"

    def __str__(self):
        return f"{self.tipo} - ${self.monto}"
