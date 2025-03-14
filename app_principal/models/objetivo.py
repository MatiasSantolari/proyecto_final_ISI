from django.db import models

class Objetivo(models.Model):
    id_objetivo = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=255)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=50)

    class Meta:
        db_table = 'objetivos'

    def __str__(self):
        return self.descripcion
