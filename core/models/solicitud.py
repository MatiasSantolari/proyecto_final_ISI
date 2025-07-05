from django.db import models
from .persona import Persona
from .cargo import Cargo
# EJ ManyToManu --> categoria = models.ManyToManyField(Categoria)
# Crea una tabla intermedia entre por ejemplo Cargo y Categoria, si un Cargo esta en muchas Categorias y viceversa
# Pero solo sirve para que quede el id de ambos, si queremos agregar mas atributos hay que crear la tabla a mano
# como ya se viene haciendo y simplemente utilizar el ForeignKey.


class Solicitud(models.Model): # Relacion Persona(en estado Postulante) con Cargo(al cual se Postula)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    fecha = models.DateField(verbose_name='Fecha Realizacion')
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, verbose_name='Estado Solicitud')

    def __str__(self):
        return self.fecha + self.persona

    class Meta:
        verbose_name = 'Solicitud'        
        verbose_name_plural = 'Solicitudes'
        db_table = 'solicitud_persona'
        constraints = [
            models.UniqueConstraint(fields=['persona', 'cargo', 'fecha'], name='unique_solicitud_por_fecha')
        ]
        ordering = ['id']  # - para oden descendente

