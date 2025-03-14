from django.db import models

class Logro(models.Model):
    id_logro = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=255)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        db_table = 'logros'  

    def __str__(self):
        return self.descripcion
