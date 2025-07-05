from django.db import models

class Descuento(models.Model):
    tipo = models.CharField(max_length=100, verbose_name='Tipo de descuento')
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto de descuento')

    class Meta:
        verbose_name = 'Descuento'
        verbose_name_plural = 'Descuentos'
        db_table = "descuento"

    def __str__(self):
        return f"{self.tipo} - ${self.monto}"
