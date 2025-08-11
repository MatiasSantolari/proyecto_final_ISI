from django.db import models
from .cargo import Cargo
from .persona import Persona


class Empleado(Persona):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('licencia', 'En licencia'),
        ('suspendido', 'Suspendido'),
        ('prueba', 'En Periodo de Prueba'),
        ('jubilado', 'Jubilado'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, verbose_name='Estado Empleado')
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    cantidad_dias_disponibles = models.IntegerField(verbose_name='Cantidad dias disponibles de vacaciones')

    class Meta:
        verbose_name = 'Empleado'        
        verbose_name_plural = 'Empleados'
        db_table = 'empleado'
        ordering = ['id']  # - para oden descendente

    def departamento_actual(self):
        cargo_activo = self.empleadocargo_set.filter(fecha_inicio__isnull=False, fecha_fin__isnull=True).first()
        if cargo_activo:
            cargo = cargo_activo.cargo
            cargo_departamento = cargo.cargodepartamento_set.first() 
            if cargo_departamento:
                return cargo_departamento.departamento
        return None




