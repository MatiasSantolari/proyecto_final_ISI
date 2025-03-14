from django.db import models
from .cargo import Cargo
from .solicitud import Solicitud

class Persona(models.Model):
    id_persona = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    email = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    fecha_nacimiento = models.DateField()
    direccion = models.CharField(max_length=255, null=True, blank=True)
    
    TIPO_PERSONA_CHOICES = [
        ('empleado', 'Empleado'),
        ('postulante', 'Postulante'),
    ]
    tipo_persona = models.CharField(max_length=10, choices=TIPO_PERSONA_CHOICES)

    cargos = models.ManyToManyField(Cargo, through=Solicitud, related_name="postulantes")

    class Meta:
        db_table = 'persona'  
