from django.db import models
from .institucion import Institucion
from .capacitacion import Capacitacion


class InstitucionCapacitacion(models.Model):
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE)
    capacitacion = models.ForeignKey(Capacitacion, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'InstitucionCapacitacion'
        verbose_name_plural = 'InstitucionesCapacitaciones'
        db_table = 'institucion_capacitacion'
        ordering = ['id']  # - para oden descendente

    def __str__(self):
        return {self.institucion} + " - " + {self.capacitacion}
