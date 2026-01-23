# En tu_app/context_processors.py

from datetime import date
from .models import HistorialAsistencia # Importa tu modelo
from django.utils import timezone

def common_attendance_data(request):
    """Agrega datos de asistencia comunes a todas las vistas."""
    if request.user.is_authenticated:
        hoy = timezone.localtime(timezone.now()).date()
        try:
            # Intenta obtener la asistencia de hoy para el usuario logueado
            asistencia_hoy = HistorialAsistencia.objects.get(
                empleado__usuario=request.user, 
                fecha_asistencia=hoy
            )
        except HistorialAsistencia.DoesNotExist:
            asistencia_hoy = None
            
        return {
            'hoy': hoy,
            'asistencia_hoy': asistencia_hoy, # Esta variable nos dice si ya registró o no
        }
    return {}
