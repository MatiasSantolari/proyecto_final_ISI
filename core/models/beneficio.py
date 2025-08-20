from django.db import models

class Beneficio(models.Model):
    descripcion = models.CharField(max_length=100, verbose_name='Descripcion del beneficio')
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto del beneficio')
    activo = models.BooleanField(default=True, verbose_name='estado de actividad')
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Porcentaje de descuento (%)', help_text='Ingrese el porcentaje entre 0 y 100')

    class Meta:
        verbose_name = 'Beneficio'
        verbose_name_plural = 'Beneficios'
        db_table = "beneficio"

    def __str__(self):
        return f"{self.descripcion} - ${self.monto}"
