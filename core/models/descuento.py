from django.db import models
from django.core.exceptions import ValidationError

class Descuento(models.Model):
    descripcion = models.CharField(max_length=100, verbose_name='Descripcion del descuento')
    monto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Monto del descuento')
    activo = models.BooleanField(default=True, verbose_name='estado de actividad')
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Porcentaje de descuento (%)', help_text='Ingrese el porcentaje entre 0 y 100')

    class Meta:
        verbose_name = 'Descuento'
        verbose_name_plural = 'Descuentos'
        db_table = "descuento"

    def clean(self):
        super().clean()
        if not self.monto and not self.porcentaje:
            raise ValidationError('Debe ingresar monto o porcentaje.')
        if self.monto and self.porcentaje:
            raise ValidationError('No puede ingresar ambos: monto y porcentaje.')
        if self.porcentaje and (self.porcentaje < 0 or self.porcentaje > 100):
            raise ValidationError('El porcentaje debe estar entre 0 y 100.')

    def __str__(self):
        valor = self.monto if self.monto else f"{self.porcentaje}%"
        return f"{self.descripcion} - {valor}"