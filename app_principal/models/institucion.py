from django.db import models

class Institucion(models.Model):
    id_institucion = models.AutoField(primary_key=True, db_column="id_institucion")
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    correo = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "institucion"

    def __str__(self):
        return self.nombre
