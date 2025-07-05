from django.db import models

class Beneficio(models.Model):
    descripcion = models.CharField(max_length=100, verbose_name='Descripcion del beneficio')
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto del beneficio')

    class Meta:
        verbose_name = 'Beneficio'
        verbose_name_plural = 'Beneficios'
        db_table = "beneficio"

    def __str__(self):
        return f"{self.descripcion} - ${self.monto}"
