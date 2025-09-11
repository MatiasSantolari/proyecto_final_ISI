from django.db import models

class TipoContrato(models.Model):
    descripcion = models.CharField(max_length=255, verbose_name='Descripcion del tipo de contrato')
    duracion_meses = models.PositiveIntegerField(null=True, blank=True, verbose_name="Duración estándar (meses)")

    class Meta:
        verbose_name = 'TipoContrato'
        verbose_name_plural = 'TiposContratos'
        db_table = 'tipo_contrato'
        ordering = ['id']

    def __str__(self):
        return self.descripcion
