from django.db import models

class Habilidad(models.Model):
    nombre = models.CharField(max_length=75, verbose_name='Nombre habilidad')
    descripcion = models.CharField(max_length=255, null=True, blank=True, verbose_name='Descripcion habilidad')

    class Meta:
        verbose_name = 'Habilidad'
        verbose_name_plural = 'Habilidades'
        db_table = 'habilidad'
        ordering = ['id']  # - para oden descendente
    
    def __str__(self):
        return self.nombre
