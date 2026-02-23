from django.db import models
from .institucion import Institucion

class Capacitacion(models.Model):
    institucion = models.ForeignKey(Institucion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Institucion")
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la capacitacion')
    descripcion = models.TextField(null=True, blank=True, verbose_name='Descripcion de la capacitacion')
    es_externo = models.BooleanField(default=False, verbose_name="¿Es curso externo?")
    url_sitio = models.URLField(null=True, blank=True, verbose_name="Link al curso")
    imagen_publicitaria = models.ImageField(upload_to='cursos/%Y/%m/%d', null=True, blank=True)
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Fecha de inicio')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha de fin')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creacion')
    activo = models.BooleanField(default=True, verbose_name="¿Esta activo el curso?")
    contenido_interno = models.BooleanField(default=False, verbose_name='¿Contenido propio de la empresa?')
    presencial = models.BooleanField(default=False, verbose_name='Es presencial')
    cupo = models.PositiveIntegerField(null=True, blank=True, verbose_name='Cantidad de cupos')
    
    class Meta:
        verbose_name = 'capacitacion'
        verbose_name_plural = 'Capacitaciones'
        db_table = "capacitacion"
        ordering = ['id']

    def __str__(self):
        return self.nombre
