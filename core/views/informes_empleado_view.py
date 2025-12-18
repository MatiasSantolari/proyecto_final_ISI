from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from ..models import *
from django.db.models import Q
import json


@login_required
def dashboard_empleado(request):
    return render(request, 'informes/dashboard_empleado.html')



@login_required
@require_POST
def marcar_objetivo_completado(request, pk):
    try:
        data = json.loads(request.body) if request.body else {}
        nuevo_estado = data.get('completado', True)
        empleado = Empleado.objects.get(id=request.user.persona.id)
        obj_emp = ObjetivoEmpleado.objects.get(id=pk, empleado=empleado)
        obj_emp.completado = nuevo_estado
        obj_emp.save()
        
        return JsonResponse({
            'status': 'ok', 
            'nuevo_estado': obj_emp.completado
        })
    except ObjetivoEmpleado.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'No se encontró la asignación'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
