from django.db import models

class CategoriaCargo(models.Model):
    id_categoria = models.AutoField(primary_key=True, db_column="id_categoria_cargo")
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = "categoria_cargo"
