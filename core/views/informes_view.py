from core.constants import ESTADO_EMPLEADO_CHOICES
from django.shortcuts import get_object_or_404, render
from datetime import date, datetime, timedelta
from django.urls import reverse
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
    
    queryset = queryset.filter(empleado__empleadocargo__fecha_fin__isnull=True)

    if dni:
        queryset = queryset.filter(empleado__dni__icontains=dni)

    if confirmado in ['true', 'false']:
        queryset = queryset.filter(confirmado=(confirmado == 'true'))
    if tardanza in ['true', 'false']:
        queryset = queryset.filter(tardanza=(tardanza == 'true'))
    
    if departamento_id:
        queryset = queryset.filter(empleado__empleadocargo__cargo__cargodepartamento__departamento__id=departamento_id,
                                    empleado__empleadocargo__fecha_fin__isnull=True)
    
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

        url_perfil = reverse('empleado_perfil_detalle', args=[asistencia.empleado.id])

        data.append({
            'nombre_completo': f"{asistencia.empleado.nombre} {asistencia.empleado.apellido}",
            'dni': asistencia.empleado.dni,
            'fecha_asistencia': asistencia.fecha_asistencia.strftime('%d-%m-%Y'),
            'hora_entrada': asistencia.hora_entrada.strftime('%H:%M:%S') if asistencia.hora_entrada else '-',
            'hora_salida': asistencia.hora_salida.strftime('%H:%M:%S') if asistencia.hora_salida else '-',
            'confirmado': asistencia.confirmado,
            'tardanza': asistencia.tardanza,
            'departamento': nombre_dep,
            'url_perfil': url_perfil
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
    estados = ESTADO_EMPLEADO_CHOICES
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
        
        url_perfil = reverse('empleado_perfil_detalle', args=[empleado.id])

        data.append({
            'id': empleado.id,
            'nombre_completo': f"{empleado.nombre} {empleado.apellido}",
            'dni': empleado.dni,
            'estado': empleado.estado,
            'departamento': nombre_dep,
            'cargo': nombre_cargo,
            'fecha_ingreso': empleado.fecha_ingreso.strftime('%d-%m-%Y'),
            'dias_vacaciones': empleado.cantidad_dias_disponibles,
            'url_perfil': url_perfil,
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




@login_required
def empleado_perfil_detalle_view(request, empleado_id):
    empleado = get_object_or_404(Empleado.objects.all(), id=empleado_id)
    cargo_activo = empleado.empleadocargo_set.filter(fecha_fin__isnull=True).first()
    departamento_activo = None
    if cargo_activo and cargo_activo.cargo.cargodepartamento_set.first():
        departamento_activo = cargo_activo.cargo.cargodepartamento_set.first().departamento
        
    return render(request, 'informes/empleado_perfil_detalle.html', {
        'empleado': empleado,
        'cargo_activo': cargo_activo,
        'departamento_activo': departamento_activo,
    })

@login_required
def api_empleado_nominas(request, empleado_id):
    nominas = Nomina.objects.filter(empleado_id=empleado_id).order_by('-fecha_generacion')
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 15)
    paginator = Paginator(nominas, per_page)

    try:
        items_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        items_page = paginator.page(1)
    data = [{
        'fecha': n.fecha_generacion.strftime('%d-%m-%Y'),
        'neto': float(n.monto_neto),
        'beneficios': float(n.total_beneficios),
        'descuentos': float(n.total_descuentos),
        'estado': n.estado,
    } for n in items_page]

    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': items_page.number,
            'has_next': items_page.has_next(),
            'has_previous': items_page.has_previous(),
        }
    }, safe=False)


@login_required
def api_empleado_evaluaciones(request, empleado_id):
    evaluaciones = EvaluacionEmpleado.objects.filter(empleado_id=empleado_id).order_by('-fecha_registro')
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 15)
    paginator = Paginator(evaluaciones, per_page)

    try:
        items_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        items_page = paginator.page(1)
    data = [{
        'fecha': e.fecha_registro.strftime('%d-%m-%Y'),
        'calificacion': float(e.calificacion_final) if e.calificacion_final is not None else 'N/A',
        'descripcion': e.evaluacion.descripcion or f"Evaluación {e.evaluacion.id}",
        'url_calificacion': f"/evaluaciones/{e.evaluacion.id}/empleados/", 
    } for e in items_page]

    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': items_page.number,
            'has_next': items_page.has_next(),
            'has_previous': items_page.has_previous(),
        }
    }, safe=False)


@login_required
def api_empleado_asistencia(request, empleado_id):
    asistencias = HistorialAsistencia.objects.filter(empleado_id=empleado_id).order_by('-fecha_asistencia')[:180]
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 15)
    paginator = Paginator(asistencias, per_page)

    try:
        items_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        items_page = paginator.page(1)

    data = [{
        'fecha': a.fecha_asistencia.strftime('%d-%m-%Y'),
        'entrada': a.hora_entrada.strftime('%H:%M') if a.hora_entrada else 'N/A',
        'salida': a.hora_salida.strftime('%H:%M') if a.hora_salida else 'N/A',
        'confirmado': a.confirmado,
        'tardanza': a.tardanza,
    } for a in items_page]
    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': items_page.number,
            'has_next': items_page.has_next(),
            'has_previous': items_page.has_previous(),
        }
    }, safe=False)


@login_required
def api_empleado_vacaciones(request, empleado_id):
    solicitudes = VacacionesSolicitud.objects.filter(empleado_id=empleado_id).order_by('-fecha_solicitud')
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 15)
    paginator = Paginator(solicitudes, per_page)

    try:
        items_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        items_page = paginator.page(1)

    data = [{
        'fecha_solicitud': s.fecha_solicitud.strftime('%d-%m-%Y'),
        'fecha_inicio': s.fecha_inicio.strftime('%d-%m-%Y'),
        'fecha_fin': s.fecha_fin.strftime('%d-%m-%Y'),
        'dias': s.cant_dias_solicitados,
        'estado': s.estado,
    } for s in items_page]

    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': items_page.number,
            'has_next': items_page.has_next(),
            'has_previous': items_page.has_previous(),
        }
    }, safe=False)



@login_required
def api_empleado_objetivos(request, empleado_id):
    tipo_filtro = request.GET.get('tipo', 'todos')
    
    queryset = ObjetivoEmpleado.objects.filter(empleado_id=empleado_id).select_related(
        'objetivo', 'objetivo__departamento', 'cargo'
    ).order_by('-fecha_asignacion')

    if tipo_filtro == 'empleado':
        queryset = queryset.filter(cargo__isnull=True)
    elif tipo_filtro == 'cargo':
        queryset = queryset.filter(cargo__isnull=False)

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 15)
    paginator = Paginator(queryset, per_page)

    try:
        items_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        items_page = paginator.page(1)

    data = []
    for item in items_page:
        tipo_label = 'Cargo' if item.cargo_id else 'Empleado'
        
        data.append({
            'titulo': item.objetivo.titulo,
            'descripcion': item.objetivo.descripcion,
            'fecha_asignacion': item.fecha_asignacion.strftime('%d-%m-%Y'),
            'fecha_limite': item.fecha_limite.strftime('%d-%m-%Y') if item.fecha_limite else 'N/A',
            'completado': item.completado,
            'departamento': item.objetivo.departamento.nombre if item.objetivo.departamento else 'Global',
            'tipo': tipo_label,
            'nombre_cargo': item.cargo.nombre if item.cargo else None 
        })

    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': items_page.number,
            'has_next': items_page.has_next(),
            'has_previous': items_page.has_previous(),
        }
    })


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

        fecha_pago_valor = nomina.fecha_pago.strftime('%d-%m-%Y') if nomina.fecha_pago else None
        url_perfil = reverse('empleado_perfil_detalle', args=[nomina.empleado.id])
        url_pago = reverse('nominas') 

        data.append({
            'id': nomina.id,
            'nombre_completo': f"{nomina.empleado.nombre} {nomina.empleado.apellido}",
            'dni': nomina.empleado.dni,
            'cargo': nombre_cargo,
            'departamento': nombre_dep,
            'fecha_generacion': nomina.fecha_generacion.strftime('%d-%m-%Y'),
            'fecha_pago': fecha_pago_valor,
            'estado': nomina.estado,
            'total_beneficios': float(nomina.total_beneficios),
            'total_descuentos': float(nomina.total_descuentos),
            'monto_neto': float(nomina.monto_neto),
            'url_perfil': url_perfil,
            'url_pago': url_pago,
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

        url_perfil = reverse('empleado_perfil_detalle', args=[ev_emp.empleado.id])

        data.append({
            'id': ev_emp.id,
            'nombre_completo': f"{ev_emp.empleado.nombre} {ev_emp.empleado.apellido}",
            'dni': ev_emp.empleado.dni,
            'calificacion_final': calificacion,
            'fecha_registro': ev_emp.fecha_registro.strftime('%d-%m-%Y'),
            'descripcion_evaluacion': ev_emp.evaluacion.descripcion or f"Evaluación {ev_emp.evaluacion.id}",
            'evaluacion_id': ev_emp.evaluacion.id,
            'url_perfil': url_perfil
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




##############################################
            ## VISTA EMPLEADO ##
##############################################
@login_required
def objetivos_detalle_view(request):
    return render(request, 'informes_vista_empleado/objetivos_detalle.html')


@login_required
def api_objetivos_detalle(request):
    
    empleado = None
    try:
        empleado = request.user.persona.empleado 
    except AttributeError:
        pass 
    
    if not empleado:
         return JsonResponse({
            'results': [],
            'pagination': {'total_pages': 0, 'current_page': 1, 'has_next': False, 'has_previous': False,}
        }, safe=False)

    filtro_tipo = request.GET.get('tipo', 'todos')
    qs_base = ObjetivoEmpleado.objects.filter(empleado=empleado)
    
    resultados_combinados = []
    hoy = date.today()

    qs_p1 = ObjetivoEmpleado.objects.none()
    if filtro_tipo in ['todos', 'no-diarios']:
        qs_p1 = qs_base.filter(
            fecha_limite__isnull=False,
            completado=False,
            fecha_limite__gte=hoy 
        ).order_by('fecha_limite')

    qs_p2 = ObjetivoEmpleado.objects.none()
    if filtro_tipo in ['todos', 'diarios']:
        qs_p2 = qs_base.filter(fecha_limite__isnull=True).order_by('-fecha_asignacion') 

    qs_p3 = ObjetivoEmpleado.objects.none()
    if filtro_tipo in ['todos', 'no-diarios']:
        qs_p3 = qs_base.filter(
            fecha_limite__isnull=False
        ).exclude(
            Q(completado=False) & Q(fecha_limite__gte=hoy)
        ).order_by('-fecha_limite') 

    resultados_combinados = list(qs_p1) + list(qs_p2) + list(qs_p3)
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 20) 
    
    try:
        page_num = int(page)
        per_page_num = int(per_page)
        start = (page_num - 1) * per_page_num
        end = start + per_page_num
        objetivos_page_list = resultados_combinados[start:end]
        
        total_items = len(resultados_combinados)
        total_pages = (total_items + per_page_num - 1) // per_page_num
        has_next = end < total_items
        has_previous = start > 0

    except ValueError:
        objetivos_page_list = []
        total_pages = 0
        page_num = 1
        has_next = False
        has_previous = False
    
    
    data = []
    for emp_objetivo in objetivos_page_list:
        
        es_diario = emp_objetivo.fecha_limite is None

        if emp_objetivo.completado:
            estado_display = 'Completado'
        else:
            if es_diario:
                if emp_objetivo.fecha_asignacion == hoy:
                    estado_display = 'Pendiente'
                else:
                    estado_display = 'No Completado'
            else:
                if emp_objetivo.fecha_limite and emp_objetivo.fecha_limite < hoy:
                     estado_display = 'Vencido'
                else:
                    estado_display = 'Pendiente'  

        data.append({
            'id': emp_objetivo.id,
            'titulo': emp_objetivo.objetivo.titulo, 
            'descripcion': emp_objetivo.objetivo.descripcion,
            'fechaLimite': emp_objetivo.fecha_limite.strftime('%Y-%m-%d') if emp_objetivo.fecha_limite else None,
            'fechaAsignacion': emp_objetivo.fecha_asignacion.strftime('%Y-%m-%d'),
            'estado': estado_display, 
        })
    
    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': total_pages,
            'current_page': page_num,
            'has_next': has_next,
            'has_previous': has_previous,
        }
    }, safe=False)




@login_required
def asistencias_detalle_view(request):
    return render(request, 'informes_vista_empleado/asistencias_detalle.html')

@login_required
def api_asistencias_detalle(request):
    empleado = None
    try:
        empleado = request.user.persona.empleado 
    except AttributeError:
        pass 
    
    if not empleado:
         return JsonResponse({'results': [], 'pagination': {'total_pages': 0, 'current_page': 1, 'has_next': False, 'has_previous': False,}}, safe=False)

    queryset = HistorialAsistencia.objects.filter(empleado=empleado).order_by('-fecha_asistencia', '-hora_entrada')

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 20) 
    paginator = Paginator(queryset, per_page)

    try:
        asistencias_page = paginator.page(page)
    except PageNotAnInteger:
        asistencias_page = paginator.page(1)
    except EmptyPage:
        asistencias_page = paginator.page(paginator.num_pages)
    
    
    data = []
    for asistencia in asistencias_page:
        data.append({
            'fecha_asistencia': asistencia.fecha_asistencia.strftime('%Y-%m-%d'),
            'hora_entrada': asistencia.hora_entrada.strftime('%H:%M') if asistencia.hora_entrada else None,
            'hora_salida': asistencia.hora_salida.strftime('%H:%M') if asistencia.hora_salida else None,
            'confirmado': asistencia.confirmado,
            'tardanza': asistencia.tardanza,
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
