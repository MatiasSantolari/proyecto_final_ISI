from django.db import models

class Descuento(models.Model):
    descripcion = models.CharField(max_length=100, verbose_name='Descripcion del descuento')
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto de descuento')
    activo = models.BooleanField(default=True, verbose_name='estado de actividad')
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Porcentaje de descuento (%)', help_text='Ingrese el porcentaje entre 0 y 100')

    class Meta:
        verbose_name = 'Descuento'
        verbose_name_plural = 'Descuentos'
        db_table = "descuento"

    def __str__(self):
        return f"{self.tipo} - ${self.monto}"
