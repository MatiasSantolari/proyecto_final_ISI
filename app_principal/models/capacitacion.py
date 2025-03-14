from django.db import models
from .institucion import Institucion
from .institucion_capacitacion import InstitucionCapacitacion

class Capacitacion(models.Model):
    id_capacitacion = models.AutoField(primary_key=True, db_column="id_capacitacion")
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    instituciones = models.ManyToManyField(Institucion, through=InstitucionCapacitacion, related_name="capacitaciones")

    class Meta:
        db_table = "capacitacion"

    def __str__(self):
        return self.nombre
