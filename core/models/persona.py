import os
from django.db import models
from datetime import datetime

class Persona(models.Model):
    nombre = models.CharField(max_length=50, verbose_name='Nombre')
    apellido = models.CharField(max_length=50, verbose_name='Apellido')
    dni = models.CharField(max_length=10, unique=True, verbose_name='Dni')

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
    


class DatoAcademico(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='datos_academicos')
    carrera = models.CharField(max_length=200)
    institucion = models.CharField(max_length=200)
    SITUACION_CHOICES = [
        ('cursando', 'Cursando'),
        ('finalizado', 'Finalizado'),
        ('abandonado', 'Abandonado'),
    ]
    situacion_academica = models.CharField(max_length=50, choices=SITUACION_CHOICES, verbose_name='Situacion Academica')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.carrera} - {self.institucion}"
    


class Certificacion(models.Model):
    persona = models.ForeignKey('Persona', on_delete=models.CASCADE, related_name='certificaciones')
    nombre = models.CharField(max_length=255)
    institucion = models.CharField(max_length=255)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} - {self.institucion}"



class ExperienciaLaboral(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='experiencias')
    cargo_exp = models.CharField(max_length=100)
    empresa = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    actualidad = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.cargo_exp} en {self.empresa}"
