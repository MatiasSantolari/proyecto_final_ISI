from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Empleado, HistorialAsistencia
from datetime import date
from django.db.models import Q
#Ejecucion manual pro consola ' python manage.py registrar_ausentes_diario '

class Command(BaseCommand):
    help = 'Registra automaticamente ausentes para todos los empleados activos del dia anterior.'

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