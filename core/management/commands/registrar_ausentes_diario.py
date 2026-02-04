from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Empleado, HistorialAsistencia
from datetime import date, timedelta
from django.db.models import Q
#Ejecucion manual pro consola ' python manage.py registrar_ausentes_diario '

class Command(BaseCommand):
    help = 'Registra automaticamente ausentes y cierra asistencias olvidadas del dia anterior.'

    def handle(self, *args, **options):
        ayer = timezone.localtime(timezone.now()).date() - timezone.timedelta(days=1)
        
        empleados_activos = Empleado.objects.filter(estado=1)
        
        ausentes_registrados = 0
        
        for e in empleados_activos:
            if not HistorialAsistencia.objects.filter(empleado=e, fecha_asistencia=ayer).exists():
                HistorialAsistencia.objects.create(
                    empleado=e,
                    fecha_asistencia=ayer,
                    hora_entrada=None,
                    hora_salida=None,
                    tardanza=False,
                    confirmado=False
                )
                ausentes_registrados += 1

        self.stdout.write(self.style.SUCCESS(f'Tarea completada. Se registraron {ausentes_registrados} ausentes para el {ayer}.'))

        
        MAX_WORK_DURATION = timedelta(hours=10)
        
        asistencias_pendientes = HistorialAsistencia.objects.filter(
            fecha_asistencia=ayer,
            hora_entrada__isnull=False,
            hora_salida__isnull=True
        )
        cerradas_automaticamente = 0
        for asistencia in asistencias_pendientes:
            entrada_dt = timezone.datetime.combine(asistencia.fecha_asistencia, asistencia.hora_entrada)
            salida_dt_automatica = entrada_dt + MAX_WORK_DURATION
            
            asistencia.hora_salida = salida_dt_automatica.time()
            asistencia.save()
            cerradas_automaticamente += 1

        self.stdout.write(self.style.SUCCESS(f'Tarea completada. Se cerraron automáticamente {cerradas_automaticamente} asistencias para el {ayer}.'))
