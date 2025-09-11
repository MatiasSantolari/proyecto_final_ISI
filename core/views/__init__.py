from .login_view import *
from .postulaciones_view import *
from .personas_view import *
from .cargos_view import *
from .habilidades_view import *
from .departamentos_view import *
from .descuentos_view import *
from .beneficios_view import *
from .objetivos_view import *
from .nominas_view import *
from .logros_view import *
from .asignar_beneficio_descuento_view import *
from .asistencia_view import *
from .vacaciones_view import *
from .contratos_view import *



def agregar_sueldo_base(request): return render(request, 'agregar_sueldo_base.html')
def calcular_bonificaciones(request): return render(request, 'calcular_bonificaciones.html')
def capacitaciones(request): return render(request, 'capacitaciones.html')
def competencias(request): return render(request, 'competencias.html')
#def contratos(request): return render(request, 'contratos.html')
def costos_de_personal(request): return render(request, 'costos_de_personal.html')
def criterios_evaluacion(request): return render(request, 'criterios_evaluacion.html')
def empleados(request): return render(request, 'empleados.html')
def evaluacion_desempeno(request): return render(request, 'evaluacion_desempeno.html')
def instituciones(request): return render(request, 'instituciones.html')
#def logros(request): return render(request, 'logros.html')
def nominas(request): return render(request, 'nominas.html')

def postulantes(request): return render(request, 'postulantes.html')
def publicar_ofertas_de_empleo(request): return render(request, 'publicar_ofertas_de_empleo.html')
def registrar_asistencia(request): return render(request, 'registrar_asistencia.html')
def solicitudes_nuevos_empleados(request): return render(request, 'solicitudes_nuevos_empleados.html')
def tipo_criterio_evaluacion(request): return render(request, 'tipo_criterio_evaluacion.html')
#def tipos_contrato(request): return render(request, 'tipos_contrato.html')
def competencias_faltantes(request): return render(request, 'competencias_faltantes.html')
def costos_de_contratacion(request): return render(request, 'costos_de_contratacion.html')
def reporte_evaluacion_desempeno(request): return render(request, 'reporte_evaluacion_desempeno.html')
def contratar_nuevo_empleado(request): return render(request, 'contratar_nuevo_empleado.html')
def ausencias_retardos(request): return render(request, 'ausencias_retardos.html')