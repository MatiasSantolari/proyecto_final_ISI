from django.db import models
from .usuario import Usuario
from .departamento import Departamento
from .cargo import Cargo

class SolicitudCargo(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    ]
    TIPOS = [
        ('EXISTENTE', 'Aumento de Cupos'),
        ('NUEVO', 'Cargo Nuevo'),
    ]
    solicitante = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    cargo_existente = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPOS, default='EXISTENTE')    
    nombre_cargo_nuevo = models.CharField(max_length=100, null=True, blank=True)
    descripcion_cargo_nuevo = models.TextField(null=True, blank=True)
    cupos = models.PositiveIntegerField(default=1)
    perfil_detallado = models.TextField()    
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    motivo_admin = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'solicitud_cargo'
        verbose_name = 'Solicitud de Cargo'
        ordering = ['-fecha_solicitud']
