from django.db import models

class Institucion(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la institucion')
    direccion = models.CharField(max_length=255, null=True, blank=True, verbose_name='Direccion de la institucion')
    telefono = models.CharField(max_length=20, null=True, blank=True, verbose_name='Telefono de la institucion')
    correo = models.CharField(max_length=100, null=True, blank=True, verbose_name='Correo de la institucion')

    class Meta:
        verbose_name = 'Institucion'
        verbose_name_plural = 'Instituciones'
        db_table = "institucion"
        ordering = ['id']

    def __str__(self):
        return self.nombre
