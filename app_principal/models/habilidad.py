from django.db import models

class Habilidad(models.Model):
    id_habilidad = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'habilidad'
    
    def __str__(self):
        return self.nombre
