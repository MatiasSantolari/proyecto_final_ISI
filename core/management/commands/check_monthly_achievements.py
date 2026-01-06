from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from django.db import transaction
from core.utils.utils import calcular_asistencia_perfecta
from core.models import Empleado, Logro, LogroEmpleado, LogroBeneficio, BeneficioEmpleadoNomina, Beneficio

class Command(BaseCommand):  #python manage.py check_monthly_achievements
    help = 'Checks perfect attendance for the previous month, assigns benefits, and prepares next month HR records.'

    def handle(self, *args, **options):
        today = date.today()
        first_day_of_month = today.replace(day=1)
        last_day_of_previous_month = first_day_of_month - timedelta(days=1)
        check_year = last_day_of_previous_month.year
        check_month = last_day_of_previous_month.month

        try:
            logro_asistencia = Logro.objects.get(tipo='ASISTENCIA_PERFECTA')
            logro_beneficio = LogroBeneficio.objects.get(logro=logro_asistencia)
            beneficio_asociado = logro_beneficio.beneficio

        except (Logro.DoesNotExist, LogroBeneficio.DoesNotExist):
            self.stdout.write(self.style.ERROR('Configuración de logro/beneficio de Asistencia Perfecta incompleta.'))
            return

        empleados = Empleado.objects.all()
        for empleado in empleados:
            had_perfect_attendance = calcular_asistencia_perfecta(empleado.id, check_year, check_month)

            with transaction.atomic():
                logro_empleado_qs = LogroEmpleado.objects.filter(
                    empleado=empleado,
                    logro=logro_asistencia,
                ).order_by('-id').first()

                if had_perfect_attendance:
                    if logro_empleado_qs and not logro_empleado_qs.completado:
                        logro_empleado_qs.completado = True
                        logro_empleado_qs.fecha_asignacion = last_day_of_previous_month
                        logro_empleado_qs.save()
                        self.stdout.write(self.style.SUCCESS(f'Logro completado para {empleado.nombre}'))
                        
                        BeneficioEmpleadoNomina.objects.create(
                            empleado=empleado,
                            beneficio=beneficio_asociado,
                            nomina=None 
                        )
                        self.stdout.write(self.style.SUCCESS(f'Beneficio asignado a {empleado.nombre}'))
                
                LogroEmpleado.objects.create(
                    empleado=empleado,
                    logro=logro_asistencia,
                    completado=False,
                    fecha_asignacion=None 
                )
        
        self.stdout.write(self.style.SUCCESS('Comprobación mensual completada y registros renovados.'))


# Ejemplo de entrada en crontab -e para ejecutar el día 1 de cada mes a la medianoche
# 0 0 1 * * /path/to/your/python /path/to/your/project/manage.py check_monthly_achievements
