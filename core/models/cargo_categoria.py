from django.db import models


class CategoriaCargo(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        db_table = 'categoria_cargo'
        ordering = ['id']  # - para oden descendente

    def __str__(self):
        return self.nombre
