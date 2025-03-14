from django.db import models
from .institucion import Institucion
from .capacitacion import Capacitacion

class InstitucionCapacitacion(models.Model):
    id_institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE, db_column="id_institucion")
    id_capacitacion = models.ForeignKey(Capacitacion, on_delete=models.CASCADE, db_column="id_capacitacion")

    class Meta:
        db_table = "institucion_capacitacion"
        unique_together = ("id_institucion", "id_capacitacion")

    def __str__(self):
        return f"{self.id_institucion.nombre} - {self.id_capacitacion.nombre}"
