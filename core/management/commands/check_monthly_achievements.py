from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from django.db import transaction
from core.utils.utils import calcular_asistencia_perfecta
from core.models import Empleado, Logro, LogroEmpleado, LogroBeneficio, BeneficioEmpleadoNomina, HistorialContrato

class Command(BaseCommand):  #python manage.py check_monthly_achievements
    help = 'Checks perfect attendance and seniority milestones to assign benefits.'

    def calcular_antiguedad_anios(self, empleado):
        """Suma la duración de todos los contratos del empleado."""
        contratos = HistorialContrato.objects.filter(empleado=empleado)
        total_dias = 0
        for contrato in contratos:
            f_inicio = contrato.fecha_inicio
            f_fin = contrato.fecha_fin if contrato.fecha_fin else date.today()
            if f_inicio and f_fin:
                total_dias += (f_fin - f_inicio).days
        return total_dias / 365.25

    def handle(self, *args, **options):
        today = date.today()
        first_day_of_month = today.replace(day=1)
        last_day_of_previous_month = first_day_of_month - timedelta(days=1)
        check_year = last_day_of_previous_month.year
        check_month = last_day_of_previous_month.month

        try:
            logro_asistencia = Logro.objects.get(tipo='ASISTENCIA_PERFECTA')
            lb_asistencia = LogroBeneficio.objects.get(logro=logro_asistencia)
            beneficio_asistencia = lb_asistencia.beneficio
        except (Logro.DoesNotExist, LogroBeneficio.DoesNotExist):
            self.stdout.write(self.style.ERROR('Configuración de Asistencia Perfecta incompleta.'))
            return

        hitos_antiguedad = {
            1: 'ANTIGUEDAD_1', 3: 'ANTIGUEDAD_3', 5: 'ANTIGUEDAD_5',
            10: 'ANTIGUEDAD_10', 15: 'ANTIGUEDAD_15', 20: 'ANTIGUEDAD_20',
            25: 'ANTIGUEDAD_25', 30: 'ANTIGUEDAD_30', 40: 'ANTIGUEDAD_40',
        }

        empleados = Empleado.objects.filter(estado=1)
        
        for empleado in empleados:
            with transaction.atomic():
                had_perfect_attendance = calcular_asistencia_perfecta(empleado.id, check_year, check_month)
                
                logro_emp_asistencia = LogroEmpleado.objects.filter(
                    empleado=empleado,
                    logro=logro_asistencia,
                ).order_by('-id').first()

                if had_perfect_attendance:
                    if logro_emp_asistencia and not logro_emp_asistencia.completado:
                        logro_emp_asistencia.completado = True
                        logro_emp_asistencia.fecha_asignacion = last_day_of_previous_month
                        logro_emp_asistencia.save()
                        
                        BeneficioEmpleadoNomina.objects.create(
                            empleado=empleado,
                            beneficio=beneficio_asistencia,
                            nomina=None 
                        )
                        self.stdout.write(self.style.SUCCESS(f'Asistencia perfecta: Beneficio para {empleado.apellido}'))
                
                LogroEmpleado.objects.create(
                    empleado=empleado,
                    logro=logro_asistencia,
                    completado=False,
                    fecha_asignacion=None 
                )

                anios = self.calcular_antiguedad_anios(empleado)
                
                hito_alcanzado_actual = None
                slug_alcanzado_actual = None

                for anios_req, slug_logro in sorted(hitos_antiguedad.items(), reverse=True):
                    if anios >= anios_req:
                        hito_alcanzado_actual = anios_req
                        slug_alcanzado_actual = slug_logro
                        break
                
                if hito_alcanzado_actual:
                    try:
                        logro_obj = Logro.objects.get(tipo=slug_alcanzado_actual)
                        
                        ya_tiene_este_hito = LogroEmpleado.objects.filter(
                            empleado=empleado, 
                            logro=logro_obj, 
                            completado=True
                        ).exists()

                        if not ya_tiene_este_hito:
                            otros_logros_antiguedad = Logro.objects.filter(
                                tipo__startswith='ANTIGUEDAD_'
                            ).exclude(tipo=slug_alcanzado_actual)

                            beneficios_viejos = BeneficioEmpleadoNomina.objects.filter(
                                empleado=empleado,
                                nomina__isnull=True, 
                                beneficio__logrobeneficio__logro__in=otros_logros_antiguedad
                            )

                            cantidad_borrados = beneficios_viejos.count()
                            beneficios_viejos.delete()

                            LogroEmpleado.objects.create(
                                empleado=empleado,
                                logro=logro_obj,
                                completado=True,
                                fecha_asignacion=today
                            )

                            lb = LogroBeneficio.objects.get(logro=logro_obj)
                            BeneficioEmpleadoNomina.objects.create(
                                empleado=empleado,
                                beneficio=lb.beneficio,
                                nomina=None
                            )

                            msg = f'Antigüedad {hito_alcanzado_actual} años: Asignado a {empleado.apellido}'
                            if cantidad_borrados > 0:
                                msg += f' (Reemplazó hito anterior)'
                            self.stdout.write(self.style.SUCCESS(msg))

                    except (Logro.DoesNotExist, LogroBeneficio.DoesNotExist):
                        pass


# Ejemplo de entrada en crontab -e para ejecutar el día 1 de cada mes a la medianoche
# 0 0 1 * * /path/to/your/python /path/to/your/project/manage.py check_monthly_achievements
