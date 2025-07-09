import os
from django.db import models
from datetime import datetime

class Persona(models.Model):
    nombre = models.CharField(max_length=50, verbose_name='Nombre')
    apellido = models.CharField(max_length=50, verbose_name='Apellido')
    dni = models.CharField(max_length=10, unique=True, verbose_name='Dni')
    email = models.CharField(max_length=50, verbose_name='Email')

    telefono = models.CharField(max_length=15, null=True, blank=True, verbose_name='Telefono')
    prefijo_pais = models.CharField(max_length=5, null=True, blank=True, verbose_name='Codigo Pais Telefono')
    
    fecha_nacimiento = models.DateField(verbose_name='Fecha de Nacimiento')
    fecha_ingreso = models.DateField(default=datetime.now, verbose_name='Fecha de ingreso')

    pais = models.CharField(max_length=50, blank=True, null=True, verbose_name='Nombre pais')
    provincia = models.CharField(max_length=50, blank=True, null=True, verbose_name='Nombre provincia')
    ciudad = models.CharField(max_length=50, blank=True, null=True, verbose_name='Nombre Ciudad')
    calle = models.CharField(max_length=50, blank=True, null=True, verbose_name='Nombre calle')
    numero = models.CharField(max_length=10, blank=True, null=True, verbose_name='Numero calle')

    genero = models.CharField(max_length=50, null=True, blank=True, verbose_name='Genero')
    avatar = models.ImageField(upload_to='avatar/%Y/%m/%d', null=True, blank=True)
    cvitae = models.FileField(upload_to='cvitae/%Y/%m/%d', null=True, blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre + self.apellido
    
    class Meta:
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        db_table = 'persona'
        ordering = ['id']  # - para oden descendente

    
    def cvitae_filename(self):
        if self.cvitae:
            return os.path.basename(self.cvitae.name)
        return ""