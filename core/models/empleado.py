from django.db import models
from .cargo import Cargo
from .persona import Persona
from core.constants import ESTADO_EMPLEADO_CHOICES
from django.core.exceptions import ValidationError


class Empleado(Persona):
    estado = models.CharField(max_length=20, choices=ESTADO_EMPLEADO_CHOICES, verbose_name='Estado Empleado')
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True)
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



    def departamento_actual_nombre(self):
        cargo_activo = self.empleadocargo_set.filter(fecha_fin__isnull=True).order_by('-fecha_inicio').first()
        if cargo_activo:
            cargo = cargo_activo.cargo
            cargo_departamento = cargo.cargodepartamento_set.first() 
            if cargo_departamento:
                return cargo_departamento.departamento.nombre
        return "-"


    def cargo_actual_nombre(self):
        cargo_activo = self.empleadocargo_set.filter(fecha_fin__isnull=True).order_by('-fecha_inicio').first()
        if cargo_activo and cargo_activo.cargo:
            return cargo_activo.cargo.nombre
        return "-"
    


    def cbu_actual_o_vacio(self):
        """Devuelve el CBU si está cargado; de lo contrario, una cadena de 22 ceros para que el banco no rebote el archivo."""
        if hasattr(self, 'datos_bancarios') and self.datos_bancarios.cbu_cuenta:
            return self.datos_bancarios.cbu_cuenta
        return "0000000000000000000000"


class DatosBancariosEmpleado(models.Model):
    empleado = models.OneToOneField(
        Empleado, 
        on_delete=models.CASCADE, 
        related_name='datos_bancarios',
        verbose_name="Empleado"
    )
    banco_nombre = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name="Entidad Bancaria"
    )
    cbu_cuenta = models.CharField(
        max_length=22, 
        null=True, 
        blank=True, 
        verbose_name="CBU Cuenta Sueldo"
    )

    class Meta:
        db_table = 'datos_bancarios_empleado'
        verbose_name = 'Datos Bancarios'
        verbose_name_plural = 'Datos Bancarios'

    def clean(self):
        super().clean()
        if self.cbu_cuenta:
            self.cbu_cuenta = self.cbu_cuenta.strip()
            if len(self.cbu_cuenta) != 22:
                raise ValidationError('El CBU debe contener exactamente 22 caracteres numéricos.')
            if not self.cbu_cuenta.isdigit():
                raise ValidationError('El CBU solo puede contener caracteres numéricos del 0 al 9.')


    def __str__(self):
        return f"{self.empleado.apellido} {self.empleado.nombre} - {self.banco_nombre}: {self.cbu_cuenta}"