from django.shortcuts import get_object_or_404, render
from datetime import date, datetime, timedelta
from ..models import *
from django.contrib.auth.decorators import login_required
import csv
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Case, When, Value, IntegerField
from django.db.models import Prefetch
from django.db.models import F 


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



## EMPLEADOS
########################
def get_empleados_queryset(request):
    estado_order = Case(
        When(estado='activo', then=Value(0)),      
        default=Value(100),                        
        output_field=IntegerField(),
    )
    queryset = Empleado.objects.all().order_by(estado_order,'apellido')
    
    dni = request.GET.get('dni')
    estado = request.GET.get('estado')
    departamento_id = request.GET.get('departamento_id')

    if dni:
        queryset = queryset.filter(dni__icontains=dni)
    if estado:
        queryset = queryset.filter(estado=estado)
    if departamento_id:
        queryset = queryset.filter(
            empleadocargo__cargo__cargodepartamento__departamento__id=departamento_id,
            empleadocargo__fecha_fin__isnull=True
        )

    return queryset.distinct()


@login_required
def empleados_detalle_view(request):
    estados = Empleado.ESTADO_CHOICES
    return render(request, 'informes/empleados_detalle.html', {'estados': estados})


@login_required
def api_empleados_detalle(request):
    queryset = get_empleados_queryset(request)
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 50)
    paginator = Paginator(queryset, per_page)

    try:
        empleados_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        empleados_page = paginator.page(1)

    data = []
    for empleado in empleados_page:

        cargo_activo = empleado.empleadocargo_set.filter(fecha_fin__isnull=True).first()
        nombre_cargo = cargo_activo.cargo.nombre if cargo_activo else 'N/A'
        nombre_dep = 'N/A'
        if cargo_activo and cargo_activo.cargo.cargodepartamento_set.first():
            nombre_dep = cargo_activo.cargo.cargodepartamento_set.first().departamento.nombre
        
        data.append({
            'id': empleado.id,
            'nombre_completo': f"{empleado.nombre} {empleado.apellido}",
            'dni': empleado.dni,
            'estado': empleado.estado,
            'departamento': nombre_dep,
            'cargo': nombre_cargo,
            'fecha_ingreso': empleado.fecha_ingreso.strftime('%d-%m-%Y'),
            'dias_vacaciones': empleado.cantidad_dias_disponibles,
        })
    
    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': empleados_page.number,
            'has_next': empleados_page.has_next(),
            'has_previous': empleados_page.has_previous(),
        }
    }, safe=False)



@login_required
def exportar_empleados_csv(request):
    queryset = get_empleados_queryset(request)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="empleados_filtrados.csv"'
    writer = csv.writer(response)
    writer.writerow(['Nombre Completo', 'DNI', 'Estado', 'Cargo Actual', 'Fecha Ingreso', 'Dias Vacaciones', 'Departamento'])
    
    for empleado in queryset:
        cargo_activo = empleado.empleadocargo_set.filter(fecha_fin__isnull=True).first()
        nombre_cargo = cargo_activo.cargo.nombre if cargo_activo else 'N/A'

        nombre_dep = 'N/A'
        if cargo_activo and cargo_activo.cargo.cargodepartamento_set.first():
            nombre_dep = cargo_activo.cargo.cargodepartamento_set.first().departamento.nombre
 
        writer.writerow([
            f"{empleado.nombre} {empleado.apellido}",
            empleado.dni,
            empleado.estado,
            nombre_cargo,
            empleado.fecha_ingreso,
            empleado.cantidad_dias_disponibles,
            nombre_dep
        ])
    return response



#############################
## NOMINAS
############
def get_nominas_queryset(request):
    queryset = Nomina.objects.select_related(
        'empleado',
    ).order_by('-fecha_generacion')
    
    dni = request.GET.get('dni')
    estado = request.GET.get('estado')
    departamento_id = request.GET.get('departamento_id')
    
    if dni:
        queryset = queryset.filter(empleado__dni__icontains=dni)
    if estado:
        queryset = queryset.filter(estado=estado)
    if departamento_id:
        queryset = queryset.filter(
            empleado__empleadocargo__cargo__cargodepartamento__departamento__id=departamento_id,
            empleado__empleadocargo__fecha_fin__isnull=True
        )

    return queryset.distinct()


@login_required
def nominas_detalle_view(request):
    estados = Nomina.ESTADO_CHOICES
    return render(request, 'informes/nominas_detalle.html', {'estados': estados})


@login_required
def api_nominas_detalle(request):
    queryset = get_nominas_queryset(request)
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 50)
    paginator = Paginator(queryset, per_page)

    try:
        nominas_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        nominas_page = paginator.page(1)

    data = []
    for nomina in nominas_page:
        cargo_activo = nomina.empleado.empleadocargo_set.filter(fecha_fin__isnull=True).first()
        nombre_cargo = cargo_activo.cargo.nombre if cargo_activo else 'N/A'
        nombre_dep = 'N/A'
        if cargo_activo and cargo_activo.cargo.cargodepartamento_set.first():
            nombre_dep = cargo_activo.cargo.cargodepartamento_set.first().departamento.nombre
        fecha_pago_formateada = '-'
        if nomina.fecha_pago:
            fecha_pago_formateada = nomina.fecha_pago.strftime('%d-%m-%Y')
        data.append({
            'id': nomina.id,
            'nombre_completo': f"{nomina.empleado.nombre} {nomina.empleado.apellido}",
            'dni': nomina.empleado.dni,
            'cargo': nombre_cargo,
            'departamento': nombre_dep,
            'fecha_generacion': nomina.fecha_generacion.strftime('%d-%m-%Y'),
            'fecha_pago': fecha_pago_formateada,
            'estado': nomina.estado,
            'total_beneficios': float(nomina.total_beneficios),
            'total_descuentos': float(nomina.total_descuentos),
            'monto_neto': float(nomina.monto_neto),
        })
    
    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': nominas_page.number,
            'has_next': nominas_page.has_next(),
            'has_previous': nominas_page.has_previous(),
        }
    }, safe=False)


@login_required
def exportar_nominas_csv(request):
    queryset = get_nominas_queryset(request)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="nominas_filtradas.csv"'
    writer = csv.writer(response)
    writer.writerow(['Nombre Completo', 'DNI', 'Cargo', 'Departamento', 'Fecha Generacion', 'Fecha Pago', 'Estado', 'Beneficios', 'Descuentos', 'Monto Neto'])
    
    for nomina in queryset:
        cargo_activo = nomina.empleado.empleadocargo_set.filter(fecha_fin__isnull=True).first()
        nombre_cargo = cargo_activo.cargo.nombre if cargo_activo else 'N/A'
        nombre_dep = 'N/A'
        if cargo_activo and cargo_activo.cargo.cargodepartamento_set.first():
            nombre_dep = cargo_activo.cargo.cargodepartamento_set.first().departamento.nombre

        writer.writerow([
            f"{nomina.empleado.nombre} {nomina.empleado.apellido}",
            nomina.empleado.dni,
            nombre_cargo,
            nombre_dep,
            nomina.fecha_generacion,
            nomina.fecha_pago,
            nomina.estado,
            nomina.total_beneficios,
            nomina.total_descuentos,
            nomina.monto_neto,
        ])
    return response



#### EVALUACIONES
#################
@login_required
def api_evaluaciones_list(request):
    evaluaciones = Evaluacion.objects.filter(activo=True).order_by('-fecha_evaluacion').values('id', 'descripcion', 'fecha_evaluacion')
    data = []
    for eval in evaluaciones:
        data.append({
            'id': eval['id'],
            'nombre': f"{eval['descripcion'] or 'Evaluación'} ({eval['fecha_evaluacion'].strftime('%Y-%m-%d')})"
        })
    return JsonResponse(data, safe=False)



def get_evaluaciones_queryset(request):
    queryset = EvaluacionEmpleado.objects.select_related(
        'empleado',
        'evaluacion'
    ).order_by('-fecha_registro', 'empleado__apellido')
    
    dni = request.GET.get('dni')
    evaluacion_id = request.GET.get('evaluacion_id')
    
    if dni:
        queryset = queryset.filter(empleado__dni__icontains=dni)
    if evaluacion_id:
        queryset = queryset.filter(evaluacion__id=evaluacion_id)

    return queryset



@login_required
def evaluaciones_detalle_view(request):
    return render(request, 'informes/evaluaciones_detalle.html')


@login_required
def api_evaluaciones_detalle(request):
    queryset = get_evaluaciones_queryset(request)
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 50)
    paginator = Paginator(queryset, per_page)

    try:
        evaluaciones_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        evaluaciones_page = paginator.page(1)

    data = []
    for ev_emp in evaluaciones_page:
        calificacion = float(ev_emp.calificacion_final) if ev_emp.calificacion_final is not None else 'Sin Calificar'
        data.append({
            'id': ev_emp.id,
            'nombre_completo': f"{ev_emp.empleado.nombre} {ev_emp.empleado.apellido}",
            'dni': ev_emp.empleado.dni,
            'calificacion_final': calificacion,
            'fecha_registro': ev_emp.fecha_registro.strftime('%d-%m-%Y'),
            'descripcion_evaluacion': ev_emp.evaluacion.descripcion or f"Evaluación {ev_emp.evaluacion.id}",
            'evaluacion_id': ev_emp.evaluacion.id
        })
    
    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': evaluaciones_page.number,
            'has_next': evaluaciones_page.has_next(),
            'has_previous': evaluaciones_page.has_previous(),
        }
    }, safe=False)


@login_required
def exportar_evaluaciones_csv(request):
    queryset = get_evaluaciones_queryset(request)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="evaluaciones_filtradas.csv"'
    writer = csv.writer(response)
    writer.writerow(['Nombre Completo', 'DNI', 'Calificacion Final', 'Fecha Registro', 'Descripcion Evaluacion'])
    
    for ev_emp in queryset:
        writer.writerow([
            f"{ev_emp.empleado.nombre} {ev_emp.empleado.apellido}",
            ev_emp.empleado.dni,
            float(ev_emp.calificacion_final) if ev_emp.calificacion_final is not None else 'N/A',
            ev_emp.fecha_registro,
            ev_emp.evaluacion.descripcion or f"Evaluación {ev_emp.evaluacion.id}",
        ])
    return response
