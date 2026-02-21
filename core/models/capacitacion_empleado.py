from django.db import models
from .capacitacion import Capacitacion
from .empleado import Empleado

class CapacitacionEmpleado(models.Model):
    ESTADO_CHOICES = [
        ('INSCRIPTO', 'Inscripto/Interesado'),
        ('EN_CURSO', 'Realizando curso'),
        ('COMPLETADO', 'Finalizado'),
        ('CANCELADO', 'Cancelado/Abandonado'),
    ]
    capacitacion = models.ForeignKey(Capacitacion, on_delete=models.CASCADE, related_name="inscripciones")
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="mis_capacitaciones")
    fecha_inscripcion = models.DateField(auto_now_add=True, verbose_name='Fecha de inscripción')
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='INSCRIPTO',
        verbose_name='Estado'
    )
    comprobante = models.FileField(upload_to='certificadosCursos/%Y/%m/%d', null=True, blank=True, verbose_name="Certificado")
    fecha_completado = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('capacitacion', 'empleado')
        verbose_name = "CapacitacionEmpleado"
        verbose_name_plural = "CapacitacionesEmpleados"
        db_table = "capacitacion_empleado"
        ordering = ['id']
