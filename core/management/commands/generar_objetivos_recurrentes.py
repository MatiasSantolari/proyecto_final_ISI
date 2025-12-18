from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Empleado, Objetivo, ObjetivoEmpleado, Cargo 

# Con lo siguiente generamos los objetivos del dia de hoy, lo ideal es que este programado en el servidor 
# para que haga la generacion sola los dias laborables a las 00:00hs
# python manage.py generar_objetivos_recurrentes 
class Command(BaseCommand):
    help = 'Genera los objetivos diarios y por cargo para los empleados'

    def handle(self, *args, **options):
        hoy = timezone.now().date()
        empleados = Empleado.objects.filter(estado='1') 
        
        creados_count = 0

        for emp in empleados:
            objetivos_recurrentes = Objetivo.objects.filter(es_recurrente=True, activo=True)
            
            for obj in objetivos_recurrentes:
                origen_cargo = emp.cargo if emp.cargo else None
                
                _, created = ObjetivoEmpleado.objects.get_or_create(
                    objetivo=obj,
                    empleado=emp,
                    fecha_asignacion=hoy,
                    defaults={
                        'completado': False,
                        'cargo': origen_cargo
                    }
                )
                if created: creados_count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Exito: Se generaron {creados_count} asignaciones de objetivos recurrentes para hoy.'))

