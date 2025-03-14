from django.db import models

class TipoCriterio(models.Model):
    id_tipo_criterio = models.AutoField(primary_key=True, db_column="id_tipo_criterio")
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "tipo_criterio"

    def __str__(self):
        return self.nombre
