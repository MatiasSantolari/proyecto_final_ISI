from django.db import models


class Competencia(models.Model):
    descripcion = models.CharField(max_length=255, verbose_name='Descripcion de la competencia')

    class Meta:
        verbose_name = "Competencia"
        verbose_name_plural = "Competencias"
        db_table = "competencia"

    def __str__(self):
        return self.descripcion
