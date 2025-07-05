from django.db import models

class TipoContrato(models.Model):
    descripcion = models.CharField(max_length=255, verbose_name='Descripcion del tipo de contrato')
    costo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Costo del tipo de contrato')

    class Meta:
        verbose_name = 'TipoContrato'
        verbose_name_plural = 'TiposContratos'
        db_table = 'tipo_contrato'
        ordering = ['id']

    def __str__(self):
        return self.descripcion
