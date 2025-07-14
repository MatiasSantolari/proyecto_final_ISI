from django.db import models
from .departamento import Departamento


class Cargo(models.Model):
    nombre = models.CharField(max_length=50, verbose_name='Nombre Cargo')
    descripcion = models.CharField(max_length=255, null=True, blank=True, verbose_name='Descripcion')
    es_jefe = models.BooleanField(default=False, verbose_name='Indentificador es Jefe')
    es_gerente = models.BooleanField(default=False, verbose_name='Indentificador es Gerente')

    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        db_table = 'cargo'
        ordering = ['id']  # (-) para oden descendente

    def __str__(self):
        return self.nombre
    
    @staticmethod
    def get_gerente_por_departamento(departamento_id):
        from .cargo_departamento import CargoDepartamento  # o donde esté definido
        relacion = CargoDepartamento.objects.filter(
            departamento_id=departamento_id,
            cargo__es_gerente=True
        ).select_related('cargo').first()
        return relacion.cargo if relacion else None