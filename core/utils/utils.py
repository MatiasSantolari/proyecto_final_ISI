import calendar
from datetime import date, timedelta
from django.utils import timezone
from ..models import Empleado, HistorialAsistencia

def calcular_asistencia_perfecta(empleado_id, year, month):  #python manage.py check_monthly_achievements
    empleado = Empleado.objects.get(id=empleado_id)
    
    start_date = date(year, month, 1)
    end_date = date(year, month, calendar.monthrange(year, month)[1])
    
    dias_laborables = 0
    dias_asistidos = 0
    
    current_day = start_date
    while current_day <= end_date:
        if current_day.weekday() not in [5, 6]:
            dias_laborables += 1
            
            asistencia_confirmada = HistorialAsistencia.objects.filter(
                empleado=empleado,
                fecha_asistencia=current_day,
                hora_entrada__isnull=False, 
                hora_salida__isnull=False,
                confirmado=True
            ).exists()

            if asistencia_confirmada:
                dias_asistidos += 1
        
        current_day += timedelta(days=1)

    return dias_asistidos > 0 and dias_asistidos == dias_laborables
