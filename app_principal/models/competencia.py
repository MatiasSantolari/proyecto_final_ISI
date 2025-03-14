from django.db import models

class Competencia(models.Model):
    id_competencia = models.AutoField(primary_key=True, db_column="id_competencia")
    descripcion = models.CharField(max_length=255)

    class Meta:
        db_table = "competencias"

    def __str__(self):
        return self.descripcion
