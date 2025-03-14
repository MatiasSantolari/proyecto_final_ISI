from django.db import models
from .persona import Persona 
from .objetivo import Objetivo
from .objetivo_empleado import ObjetivoEmpleado 
from .logro import Logro
from .logro_empleado import LogroEmpleado
from .habilidad_empleado import HabilidadEmpleado
from .habilidad import Habilidad
from .capacitacion_empleado import CapacitacionEmpleado
from .capacitacion import Capacitacion
from .competencia import Competencia
from .competencia_empleado import CompetenciaEmpleado
from .tipo_contrato import TipoContrato
from .historial_contrato import HistorialContrato
from .cargo import Cargo
from .empleado_cargo import EmpleadoCargo
from .nomina import Nomina
from .descuento import Descuento
from .descuento_empleado_nomina import DescuentoEmpleadoNomina
from .beneficio import Beneficio
from .beneficio_empleado_nomina import BeneficioEmpleadoNomina

class Empleado(Persona):  
    id_empleado = models.AutoField(primary_key=True)
    
    ESTADO_CHOICES = [
        ('inactivo', 'Inactivo'),
        ('en licencia', 'En licencia'),
        ('suspendido', 'Suspendido'),
        ('en prueba', 'En Prueba'),
        ('jubilado', 'Jubilado'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)

    habilidades = models.ManyToManyField(Habilidad, through=HabilidadEmpleado, related_name="empleados")
    logros = models.ManyToManyField(Logro, through=LogroEmpleado, related_name="empleados")
    objetivos = models.ManyToManyField(Objetivo, through=ObjetivoEmpleado, related_name="empleados")
    capacitaciones = models.ManyToManyField(Capacitacion, through=CapacitacionEmpleado, related_name="empleados")
    competencias = models.ManyToManyField(Competencia, through=CompetenciaEmpleado, related_name="empleados")
    contratos = models.ManyToManyField(TipoContrato, through=HistorialContrato, related_name="empleados")
    cargos = models.ManyToManyField(Cargo, through=EmpleadoCargo, related_name="empleados")
    nominas = models.ManyToManyField(Nomina, through=DescuentoEmpleadoNomina, related_name="empleados")
    descuentos = models.ManyToManyField(Descuento, through=DescuentoEmpleadoNomina, related_name="empleados")
    nominas = models.ManyToManyField(Nomina, through=BeneficioEmpleadoNomina, related_name="empleados")
    beneficios = models.ManyToManyField(Beneficio, through=BeneficioEmpleadoNomina, related_name="empleados")
    
    class Meta:
        db_table = 'empleado'  

    def __str__(self):
        return f"{self.nombre} {self.apellido}"