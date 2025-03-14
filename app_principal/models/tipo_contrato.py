from django.db import models

class TipoContrato(models.Model):
    id_contrato = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=255)
    costo = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'tipo_contrato'

    def __str__(self):
        return self.descripcion
