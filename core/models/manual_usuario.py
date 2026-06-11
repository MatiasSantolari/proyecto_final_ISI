from django.db import models

class ManualSistema(models.Model):
    ROLES_CHOICES = [
        ('admin', 'Administrador'),
        ('gerente', 'Gerente'),
        ('jefe', 'Jefe'),
        ('empleado', 'Empleado'),
        ('normal', 'Normal / Postulante'),
    ]
    rol = models.CharField(max_length=20, choices=ROLES_CHOICES, unique=True)
    archivo = models.FileField(upload_to='manuales/')
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Manual para {self.get_rol_display()}"
