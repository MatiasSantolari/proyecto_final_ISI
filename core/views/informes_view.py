from django.shortcuts import render
from datetime import date, datetime, timedelta
from ..models import *
from django.contrib.auth.decorators import login_required
import csv
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Prefetch


@login_required
def cambiar_tema(request):
    nuevo_tema = request.GET.get("tema")
    request.user.tema = nuevo_tema
    request.user.save()
    return JsonResponse({"status": "ok"})


@login_required
def dashboard_view(request):
    return render(request, "dashboard/dashboard.html", {})



def get_asistencias_queryset(request):
    queryset = HistorialAsistencia.objects.order_by('-fecha_asistencia', 'hora_entrada')

    dni = request.GET.get('dni')
    confirmado = request.GET.get('confirmado')
    tardanza = request.GET.get('tardanza')
    departamento_id = request.GET.get('departamento_id')

    if dni:
        queryset = queryset.filter(empleado__dni__icontains=dni)

    if confirmado in ['true', 'false']:
        queryset = queryset.filter(confirmado=(confirmado == 'true'))
    if tardanza in ['true', 'false']:
        queryset = queryset.filter(tardanza=(tardanza == 'true'))
    
    if departamento_id:
        queryset = queryset.filter(empleado__empleadocargo__cargo__cargodepartamento__departamento__id=departamento_id,
                                   empleado__empleadocargo__fecha_fin__isnull=True)
    else:
        queryset = queryset.filter(empleado__empleadocargo__fecha_fin__isnull=True)

    return queryset.distinct()



@login_required
def asistencias_detalle_view(request):
    return render(request, 'informes/asistencias_detalle.html')


@login_required
def api_departamentos_list(request):
    departamentos = Departamento.objects.all().values('id', 'nombre')
    return JsonResponse(list(departamentos), safe=False)



@login_required
def api_asistencias_detalle(request):
    queryset = get_asistencias_queryset(request) 
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 50)
    
    paginator = Paginator(queryset, per_page)

    try:
        asistencias_page = paginator.page(page)
    except PageNotAnInteger:
        asistencias_page = paginator.page(1)
    except EmptyPage:
        asistencias_page = paginator.page(paginator.num_pages)

    data = []
    for asistencia in asistencias_page:

        cargo_activo = asistencia.empleado.empleadocargo_set.filter(fecha_fin__isnull=True).first()
        
        if cargo_activo:
            nombre_dep = cargo_activo.cargo.cargodepartamento_set.first().departamento.nombre if cargo_activo.cargo.cargodepartamento_set.first() else 'N/A'
        else:
            nombre_dep = 'Sin Cargo Activo'

        data.append({
            'nombre_completo': f"{asistencia.empleado.nombre} {asistencia.empleado.apellido}",
            'dni': asistencia.empleado.dni,
            'fecha_asistencia': asistencia.fecha_asistencia.strftime('%d-%m-%Y'),
            'hora_entrada': asistencia.hora_entrada.strftime('%H:%M:%S') if asistencia.hora_entrada else '-',
            'hora_salida': asistencia.hora_salida.strftime('%H:%M:%S') if asistencia.hora_salida else '-',
            'confirmado': asistencia.confirmado,
            'tardanza': asistencia.tardanza,
            'departamento': nombre_dep 
        })
    
    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': asistencias_page.number,
            'has_next': asistencias_page.has_next(),
            'has_previous': asistencias_page.has_previous(),
        }
    }, safe=False)




@login_required
def exportar_asistencias_csv(request):
    queryset = get_asistencias_queryset(request) 
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="asistencias_filtradas.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Nombre Completo', 'DNI', 'Fecha Asistencia', 'Hora Entrada', 'Hora Salida', 'Confirmado', 'Tardanza'])
    
    for asistencia in queryset:
        writer.writerow([
            f"{asistencia.empleado.nombre} {asistencia.empleado.apellido}",
            asistencia.empleado.dni,
            asistencia.fecha_asistencia,
            asistencia.hora_entrada if asistencia.hora_entrada else 'N/A',
            asistencia.hora_salida if asistencia.hora_salida else 'N/A',
            'Si' if asistencia.confirmado else 'No',
            'Si' if asistencia.tardanza else 'No',
        ])
    return response


def exportar_asistencias_pdf(request):
    return HttpResponse("Funcionalidad PDF pendiente de implementación.", status=501)
