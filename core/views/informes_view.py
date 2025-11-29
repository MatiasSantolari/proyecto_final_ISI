from django.shortcuts import render
from django.http import JsonResponse
from datetime import date, datetime, timedelta
from ..models import *
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator



## ASISTENCIAS ##
@login_required
def dashboard_asistencias_data(request):
    departamento_id = request.GET.get('departamento')
    periodo = request.GET.get('periodo', 'hoy')

    hoy = date.today()
    if periodo == 'hoy':
        fecha_inicio = hoy
    elif periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
    elif periodo == 'mes':
        fecha_inicio = hoy - timedelta(days=30)
    elif periodo == 'año':
        fecha_inicio = hoy - timedelta(days=365)
    else:
        fecha_inicio = None


    empleados_qs = Empleado.objects.all()
    if departamento_id:
        empleados_qs = empleados_qs.filter(
            cargo__cargodepartamento__departamento_id=departamento_id
        ).distinct()

    total_empleados = empleados_qs.count()


    asistencias_qs = HistorialAsistencia.objects.filter(empleado__in=empleados_qs)
    if fecha_inicio:
        asistencias_qs = asistencias_qs.filter(fecha_asistencia__gte=fecha_inicio)


    total_asistencias = 0
    total_tardanzas = 0
    total_ausencias = 0

    for h in asistencias_qs:
        if h.hora_entrada is None:
            total_ausencias += 1
        elif h.tardanza:
            total_tardanzas += 1
        else:
            total_asistencias += 1


    empleados_con_asistencia = asistencias_qs.values_list('empleado_id', flat=True).distinct()
    total_ausencias += empleados_qs.exclude(id__in=empleados_con_asistencia).count()

    total_registros = asistencias_qs.count()

    return JsonResponse({
        'total_empleados': total_empleados,
        'total_registros': total_registros,
        'asistencias': total_asistencias,
        'tardanzas': total_tardanzas,
        'ausencias': total_ausencias,
    })



@login_required
def informe_asistencias(request):
    departamentos = Departamento.objects.all()
    return render(request, 'informe_asistencias.html', {'departamentos': departamentos})



@login_required
def informe_asistencias_data(request):
    departamento_id = request.GET.get('departamento')
    periodo = request.GET.get('periodo', 'hoy')
    pagina = int(request.GET.get('page', 1))

    hoy = date.today()
    if periodo == 'hoy':
        fecha_inicio = hoy
    elif periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
    elif periodo == 'mes':
        fecha_inicio = hoy - timedelta(days=30)
    elif periodo == 'año':
        fecha_inicio = hoy - timedelta(days=365)
    else:
        fecha_inicio = None


    empleados = Empleado.objects.all()
    if departamento_id:
        empleados = empleados.filter(
            cargo__cargodepartamento__departamento_id=departamento_id
        ).distinct()


    asistencias_qs = HistorialAsistencia.objects.select_related('empleado').all()
    if fecha_inicio:
        asistencias_qs = asistencias_qs.filter(fecha_asistencia__gte=fecha_inicio)
    if departamento_id:
        asistencias_qs = asistencias_qs.filter(empleado__in=empleados)

    detalle = []
    deptos = {}

    for h in asistencias_qs:
        dept_nombre = h.empleado.departamento_actual_nombre() or "-"

        if h.hora_entrada is None:
            ausente = True
            tardanza = False
            asistencia = False
        elif h.tardanza:
            ausente = False
            tardanza = True
            asistencia = False
        else:
            ausente = False
            tardanza = False
            asistencia = True

        detalle.append({
            'empleado': str(h.empleado),
            'departamento': dept_nombre,
            'fecha': h.fecha_asistencia.strftime('%Y-%m-%d'),
            'hora_entrada': h.hora_entrada.strftime('%H:%M') if h.hora_entrada else None,
            'hora_salida': h.hora_salida.strftime('%H:%M') if h.hora_salida else None,
            'tardanza': tardanza,
            'asistencia': asistencia,
            'ausente': ausente,
            'confirmado': h.confirmado
        })

        if dept_nombre not in deptos:
            deptos[dept_nombre] = {'asistencias': 0, 'tardanzas': 0, 'ausencias': 0}

        if ausente:
            deptos[dept_nombre]['ausencias'] += 1
        elif tardanza:
            deptos[dept_nombre]['tardanzas'] += 1
        else:
            deptos[dept_nombre]['asistencias'] += 1

    paginator = Paginator(detalle, 20)
    page_obj = paginator.get_page(pagina)

    
    total_asistencias = 0
    total_tardanzas = 0
    total_ausencias = 0

    empleados_qs = Empleado.objects.all()
    if departamento_id:
        empleados_qs = empleados_qs.filter(
            cargo__cargodepartamento__departamento_id=departamento_id
        ).distinct()

    total_empleados = empleados_qs.count()

    for h in asistencias_qs:
        if h.hora_entrada is None:
            total_ausencias += 1
        elif h.tardanza:
            total_tardanzas += 1
        else:
            total_asistencias += 1

    empleados_con_asistencia = asistencias_qs.values_list('empleado_id', flat=True).distinct()
    total_ausencias += empleados_qs.exclude(id__in=empleados_con_asistencia).count()

    total_registros = asistencias_qs.count()



    data = {
        'detalle': list(page_obj.object_list),
        'asistencias': sum(d['asistencias'] for d in deptos.values()),
        'tardanzas': sum(d['tardanzas'] for d in deptos.values()),
        'ausencias': sum(d['ausencias'] for d in deptos.values()),
        'departamentos_labels': list(deptos.keys()),
        'departamentos_asistencias': [d['asistencias'] for d in deptos.values()],
        'departamentos_tardanzas': [d['tardanzas'] for d in deptos.values()],
        'departamentos_ausencias': [d['ausencias'] for d in deptos.values()],
        'total_empleados': total_empleados,
        'total_registros': total_registros,
        'asistencias': total_asistencias,
        'tardanzas': total_tardanzas,
        'ausencias': total_ausencias,
        'paginator': {
            'num_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        }
    }

    return JsonResponse(data)




################
################
## VACACIONES ##

@login_required
def dashboard_vacaciones_data(request):
    departamento_id = request.GET.get('departamento')
    periodo = request.GET.get('periodo', 'hoy')

    hoy = date.today()
    if periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
    elif periodo == 'mes':
        fecha_inicio = hoy - timedelta(days=30)
    elif periodo == 'año':
        fecha_inicio = hoy - timedelta(days=365)
    else:
        fecha_inicio = None

    empleados_qs = Empleado.objects.all()
    if departamento_id:
        empleados_qs = empleados_qs.filter(
            cargo__cargodepartamento__departamento_id=departamento_id
        ).distinct()

    total_empleados = empleados_qs.count()

    solicitudes_qs = VacacionesSolicitud.objects.filter(empleado__in=empleados_qs)
    if fecha_inicio:
        solicitudes_qs = solicitudes_qs.filter(fecha_solicitud__gte=fecha_inicio)

    total_solicitudes = solicitudes_qs.count()
    total_aprobadas = solicitudes_qs.filter(estado='aprobado').count()
    total_pendientes = solicitudes_qs.filter(estado='pendiente').count()
    total_rechazadas = solicitudes_qs.filter(estado='rechazado').count()
    total_canceladas = solicitudes_qs.filter(estado='cancelado').count()

    return JsonResponse({
        'total_empleados': total_empleados,
        'total_solicitudes': total_solicitudes,
        'aprobadas': total_aprobadas,
        'pendientes': total_pendientes,
        'rechazadas': total_rechazadas,
        'canceladas': total_canceladas
    })



@login_required
def informe_vacaciones(request):
    departamentos = Departamento.objects.all()
    return render(request, 'informe_vacaciones.html', {'departamentos': departamentos})


@login_required
def informe_vacaciones_data(request):
    departamento_id = request.GET.get('departamento')
    periodo = request.GET.get('periodo', 'hoy')
    pagina = int(request.GET.get('page', 1))

    hoy = date.today()
    if periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
    elif periodo == 'mes':
        fecha_inicio = hoy - timedelta(days=30)
    elif periodo == 'año':
        fecha_inicio = hoy - timedelta(days=365)
    else:
        fecha_inicio = None

    empleados_qs = Empleado.objects.all()
    if departamento_id:
        empleados_qs = empleados_qs.filter(
            cargo__cargodepartamento__departamento_id=departamento_id
        ).distinct()

    solicitudes_qs = VacacionesSolicitud.objects.select_related('empleado').filter(empleado__in=empleados_qs)
    if fecha_inicio:
        solicitudes_qs = solicitudes_qs.filter(fecha_solicitud__gte=fecha_inicio)

    detalle = []
    deptos = {}

    for s in solicitudes_qs:
        dept_nombre = s.empleado.departamento_actual_nombre() or "-"
        if dept_nombre not in deptos:
            deptos[dept_nombre] = {'aprobado':0, 'pendiente':0, 'rechazado':0, 'cancelado':0}

        deptos[dept_nombre][s.estado] += 1

        detalle.append({
            'empleado': str(s.empleado),
            'departamento': dept_nombre,
            'fecha_solicitud': s.fecha_solicitud.strftime('%Y-%m-%d'),
            'fecha_inicio': s.fecha_inicio.strftime('%Y-%m-%d') if s.fecha_inicio else '-',
            'fecha_fin': s.fecha_fin.strftime('%Y-%m-%d') if s.fecha_fin else '-',
            'dias': s.cant_dias_solicitados,
            'estado': s.estado.capitalize()
        })

    paginator = Paginator(detalle, 20)
    page_obj = paginator.get_page(pagina)

    total_empleados = empleados_qs.count()
    total_solicitudes = solicitudes_qs.count()
    total_aprobadas = solicitudes_qs.filter(estado='aprobado').count()
    total_pendientes = solicitudes_qs.filter(estado='pendiente').count()
    total_rechazadas = solicitudes_qs.filter(estado='rechazado').count()
    total_canceladas = solicitudes_qs.filter(estado='cancelado').count()

    data = {
        'detalle': list(page_obj.object_list),
        'aprobadas': total_aprobadas,
        'pendientes': total_pendientes,
        'rechazadas': total_rechazadas,
        'canceladas': total_canceladas,
        'departamentos_labels': list(deptos.keys()),
        'departamentos_aprobadas': [d['aprobado'] for d in deptos.values()],
        'departamentos_pendientes': [d['pendiente'] for d in deptos.values()],
        'departamentos_rechazadas': [d['rechazado'] for d in deptos.values()],
        'departamentos_canceladas': [d['cancelado'] for d in deptos.values()],
        'total_empleados': total_empleados,
        'total_solicitudes': total_solicitudes,
        'paginator': {
            'num_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        }
    }

    return JsonResponse(data)



#############################
@login_required
def cambiar_tema(request):
    nuevo_tema = request.GET.get("tema")
    request.user.tema = nuevo_tema
    request.user.save()
    return JsonResponse({"status": "ok"})


####################
@login_required
def dashboard_view(request):
    return render(request, "dashboard/dashboard.html", {})
