from core.constants import ESTADO_EMPLEADO_CHOICES
from django.shortcuts import get_object_or_404, render, redirect
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
from django.http import JsonResponse
import json
from django.contrib import messages


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
    rol_actual = request.session.get('rol_actual', request.user.rol)

    dni = request.GET.get('dni')
    confirmado = request.GET.get('confirmado')
    tardanza = request.GET.get('tardanza')
    departamento_id = request.GET.get('departamento_id')
    
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    ausencia = request.GET.get('ausencia')
    
    queryset = queryset.filter(empleado__empleadocargo__fecha_fin__isnull=True)

    if rol_actual in ['jefe', 'gerente']:
        try:
            depto_usuario = request.user.persona.empleado.departamento_actual()
            if depto_usuario:
                queryset = queryset.filter(
                    empleado__empleadocargo__cargo__cargodepartamento__departamento=depto_usuario
                )
            else:
                return HistorialAsistencia.objects.none()
        except (AttributeError, Empleado.DoesNotExist):
            return HistorialAsistencia.objects.none()
    
    elif departamento_id and departamento_id != 'todos':
        queryset = queryset.filter(
            empleado__empleadocargo__cargo__cargodepartamento__departamento__id=departamento_id
        )

    if dni:
        queryset = queryset.filter(empleado__dni__icontains=dni)
    if confirmado in ['true', 'false']:
        queryset = queryset.filter(confirmado=(confirmado == 'true'))
    if tardanza in ['true', 'false']:
        queryset = queryset.filter(tardanza=(tardanza == 'true'))
        
    if fecha_desde:
        queryset = queryset.filter(fecha_asistencia__gte=fecha_desde)
    if fecha_hasta:
        queryset = queryset.filter(fecha_asistencia__lte=fecha_hasta)
        
    if ausencia == 'true':
        queryset = queryset.filter(hora_entrada__isnull=True, hora_salida__isnull=True, licencia=False)
    elif ausencia == 'false':
        queryset = queryset.filter(Q(hora_entrada__isnull=False) | Q(hora_salida__isnull=False) | Q(licencia=True))
    
    return queryset.distinct()




@login_required
def asistencias_detalle_view(request):
    return render(request, 'informes/asistencias_detalle.html')


@login_required
def api_departamentos_list(request):
    rol_actual = request.session.get('rol_actual', request.user.rol)
    
    if rol_actual in ['jefe', 'gerente']:
        try:
            depto = request.user.persona.empleado.departamento_actual()
            if depto:
                departamentos = Departamento.objects.filter(id=depto.id).values('id', 'nombre')
            else:
                departamentos = []
        except (AttributeError, Empleado.DoesNotExist):
            departamentos = []
    else:
        departamentos = Departamento.objects.all().values('id', 'nombre')
        
    return JsonResponse(list(departamentos), safe=False)



@login_required
def api_asistencias_detalle(request):
    queryset = get_asistencias_queryset(request) 
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 12)
    
    paginator = Paginator(queryset, per_page)

    try:
        asistencias_page = paginator.page(page)
    except PageNotAnInteger:
        asistencias_page = paginator.page(1)
    except EmptyPage:
        asistencias_page = paginator.page(paginator.num_pages)

    rango_paginas = list(paginator.get_elided_page_range(asistencias_page.number, on_each_side=2, on_ends=1))

    data = []
    for asistencia in asistencias_page:
        cargo_activo = asistencia.empleado.empleadocargo_set.filter(fecha_fin__isnull=True).first()
        
        if cargo_activo:
            nombre_dep = cargo_activo.cargo.cargodepartamento_set.first().departamento.nombre if cargo_activo.cargo.cargodepartamento_set.first() else 'N/A'
        else:
            nombre_dep = 'Sin Cargo Activo'

        url_perfil = reverse('empleado_perfil_detalle', args=[asistencia.empleado.id])

        entrada_txt = "Licencia" if asistencia.licencia else (asistencia.hora_entrada.strftime('%H:%M:%S') if asistencia.hora_entrada else '-')
        salida_txt = "Licencia" if asistencia.licencia else (asistencia.hora_salida.strftime('%H:%M:%S') if asistencia.hora_salida else '-')

        data.append({
            'nombre_completo': f"{asistencia.empleado.nombre} {asistencia.empleado.apellido}",
            'dni': asistencia.empleado.dni,
            'fecha_asistencia': asistencia.fecha_asistencia.strftime('%d-%m-%Y'),
            'hora_entrada': entrada_txt,
            'hora_salida': salida_txt,
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
            'rango_paginas': rango_paginas,
        }
    }, safe=False)



@login_required
def exportar_asistencias_csv(request):
    queryset = get_asistencias_queryset(request) 
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="asistencias_filtradas.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Nombre Completo', 'DNI', 'Departamento', 'Fecha Asistencia', 'Hora Entrada', 'Hora Salida', 'Confirmado', 'Tardanza'])
    
    for asistencia in queryset:
        cargo_activo = asistencia.empleado.empleadocargo_set.filter(fecha_fin__isnull=True).first()
        if cargo_activo:
            nombre_dep = cargo_activo.cargo.cargodepartamento_set.first().departamento.nombre if cargo_activo.cargo.cargodepartamento_set.first() else 'N/A'
        else:
            nombre_dep = 'Sin Cargo Activo'

        if asistencia.licencia:
            entrada_csv = 'Licencia Justificada'
            salida_csv = 'Licencia Justificada'
        else:
            entrada_csv = asistencia.hora_entrada if asistencia.hora_entrada else 'Ausencia'
            salida_csv = asistencia.hora_salida if asistencia.hora_salida else 'Ausencia'

        writer.writerow([
            f"{asistencia.empleado.nombre} {asistencia.empleado.apellido}",
            asistencia.empleado.dni,
            nombre_dep, 
            asistencia.fecha_asistencia,
            entrada_csv, 
            salida_csv,
            'Sí' if asistencia.confirmado else 'No',
            'Sí' if asistencia.tardanza else 'No',
        ])
    return response


def exportar_asistencias_pdf(request):
    return HttpResponse("Funcionalidad PDF pendiente de implementación.", status=501)



## EMPLEADOS
########################
def get_empleados_queryset(request):
    rol_actual = request.session.get('rol_actual', request.user.rol)
    
    estado_order = Case(
        When(estado='activo', then=Value(0)),      
        default=Value(100),                        
        output_field=IntegerField(),
    )
    
    queryset = Empleado.objects.all().order_by(estado_order, 'apellido')
    
    dni = request.GET.get('dni')
    estado = request.GET.get('estado')
    departamento_id = request.GET.get('departamento_id')

    if rol_actual in ['jefe', 'gerente']:
        try:
            depto_usuario = request.user.persona.empleado.departamento_actual()
            if depto_usuario:
                queryset = queryset.filter(
                    empleadocargo__cargo__cargodepartamento__departamento=depto_usuario,
                    empleadocargo__fecha_fin__isnull=True
                )
            else:
                return Empleado.objects.none()
        except (AttributeError, Empleado.DoesNotExist):
            return Empleado.objects.none()
            
    elif departamento_id:
        queryset = queryset.filter(
            empleadocargo__cargo__cargodepartamento__departamento__id=departamento_id,
            empleadocargo__fecha_fin__isnull=True
        )

    if dni:
        queryset = queryset.filter(dni__icontains=dni)
    if estado:
        queryset = queryset.filter(estado=estado)

    return queryset.distinct()



@login_required
def empleados_detalle_view(request):
    estados = ESTADO_EMPLEADO_CHOICES
    return render(request, 'informes/empleados_detalle.html', {'estados': estados})


@login_required
def api_empleados_detalle(request):
    queryset = get_empleados_queryset(request)
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
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


################# PERFIL PERSONA RESUMIDO ###################

@login_required
def empleado_perfil_detalle_view(request, empleado_id):
    """
    Vista principal que renderiza el perfil del empleado con sus pestañas HTML.
    """
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    cargo_activo = empleado.empleadocargo_set.filter(fecha_fin__isnull=True).first()
    departamento_activo = None
    if cargo_activo and cargo_activo.cargo.cargodepartamento_set.first():
        departamento_activo = cargo_activo.cargo.cargodepartamento_set.first().departamento
        
    todas_las_habilidades = Habilidad.objects.filter(activo=True).order_by('nombre')
    
    habilidades_asignadas = empleado.habilidadempleado_set.all().select_related('habilidad')

    return render(request, 'informes/empleado_perfil_detalle.html', {
        'empleado': empleado,
        'cargo_activo': cargo_activo,
        'departamento_activo': departamento_activo,
        'todas_las_habilidades': todas_las_habilidades, 
        'habilidades_asignadas': habilidades_asignadas,
    })



@login_required
def api_empleado_nominas(request, empleado_id):
    """
    API 1: Historial de nóminas liquidadas del empleado.
    """
    rol_actual = request.session.get('rol_actual', request.user.rol)
    
    if rol_actual in ['jefe', 'gerente']:
        depto_usuario = request.user.persona.empleado.departamento_actual()
        es_de_su_equipo = EmpleadoCargo.objects.filter(
            empleado_id=empleado_id,
            cargo__cargodepartamento__departamento=depto_usuario,
            fecha_fin__isnull=True
        ).exists()
        
        if not es_de_su_equipo:
            return JsonResponse({'error': 'No tiene permiso para ver este empleado'}, status=403)
    
    nominas = Nomina.objects.filter(empleado_id=empleado_id).order_by('-fecha_generacion')
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
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

    rango_paginas = list(paginator.get_elided_page_range(items_page.number, on_each_side=1, on_ends=1))

    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': items_page.number,
            'has_next': items_page.has_next(),
            'has_previous': items_page.has_previous(),
            'rango_paginas': rango_paginas,  
        }
    }, safe=False)


@login_required
def api_empleado_evaluaciones(request, empleado_id):
    """
    API 2: Historial de evaluaciones de desempeño del empleado.
    """
    rol_actual = request.session.get('rol_actual', request.user.rol)
    
    if rol_actual in ['jefe', 'gerente']:
        depto_usuario = request.user.persona.empleado.departamento_actual()
        es_de_su_equipo = EmpleadoCargo.objects.filter(
            empleado_id=empleado_id,
            cargo__cargodepartamento__departamento=depto_usuario,
            fecha_fin__isnull=True
        ).exists()
        
        if not es_de_su_equipo:
            return JsonResponse({'error': 'No tiene permiso para ver este empleado'}, status=403)
  
    evaluaciones = EvaluacionEmpleado.objects.filter(empleado_id=empleado_id).select_related('evaluacion').order_by('-fecha_registro')
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    paginator = Paginator(evaluaciones, per_page)
    try:
        items_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        items_page = paginator.page(1)

    data = []
    for e in items_page:
        desc_base = e.evaluacion.descripcion or f"Evaluación {e.evaluacion.id}"
        desc_final = desc_base if e.evaluacion.activo else f"{desc_base} (Inactivo)"

        data.append({
            'fecha': e.fecha_registro.strftime('%d-%m-%Y'),
            'calificacion': float(e.calificacion_final) if e.calificacion_final is not None else 'N/A',
            'descripcion': desc_final, 
            'url_calificacion': f"/evaluaciones/{e.evaluacion.id}/empleados/", 
        })

    rango_paginas = list(paginator.get_elided_page_range(items_page.number, on_each_side=1, on_ends=1))

    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': items_page.number,
            'has_next': items_page.has_next(),
            'has_previous': items_page.has_previous(),
            'rango_paginas': rango_paginas,  
        }
    }, safe=False)


def es_subordinado(user, empleado_id, rol):
    """Auxiliar para verificar si un jefe tiene acceso a un empleado."""
    if rol in ['admin']: return True
    try:
        depto_usuario = user.persona.empleado.departamento_actual()
        if not depto_usuario: return False
        return EmpleadoCargo.objects.filter(
            empleado_id=empleado_id,
            cargo__cargodepartamento__departamento=depto_usuario,
            fecha_fin__isnull=True
        ).exists()
    except:
        return False


@login_required
def api_empleado_asistencia(request, empleado_id):
    """
    API 3: Historial de asistencia diaria del empleado (Soporta Licencias).
    """
    rol = request.session.get('rol_actual', request.user.rol)
    if not es_subordinado(request.user, empleado_id, rol):
        return JsonResponse({'error': 'Acceso denegado'}, status=403)

    asistencias = HistorialAsistencia.objects.filter(empleado_id=empleado_id).order_by('-fecha_asistencia')[:180]

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    paginator = Paginator(asistencias, per_page)

    try:
        items_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        items_page = paginator.page(1)

    data = []
    for a in items_page:
        entrada_txt = "Licencia" if a.licencia else (a.hora_entrada.strftime('%H:%M') if a.hora_entrada else 'N/A')
        salida_txt = "Licencia" if a.licencia else (a.hora_salida.strftime('%H:%M') if a.hora_salida else 'N/A')

        data.append({
            'fecha': a.fecha_asistencia.strftime('%d-%m-%Y'),
            'entrada': entrada_txt,
            'salida': salida_txt,
            'confirmado': a.confirmado,
            'tardanza': a.tardanza,
            'es_licencia': a.licencia, 
        })

    rango_paginas = list(paginator.get_elided_page_range(items_page.number, on_each_side=1, on_ends=1))

    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': items_page.number,
            'has_next': items_page.has_next(),
            'has_previous': items_page.has_previous(),
            'rango_paginas': rango_paginas, 
        }
    }, safe=False)


@login_required
def api_empleado_vacaciones(request, empleado_id):
    """
    API 4: Historial de solicitudes de vacaciones del empleado.
    """
    rol = request.session.get('rol_actual', request.user.rol)
    if not es_subordinado(request.user, empleado_id, rol):
        return JsonResponse({'error': 'Acceso denegado'}, status=403)

    solicitudes = VacacionesSolicitud.objects.filter(empleado_id=empleado_id).order_by('-fecha_solicitud')

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
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

    rango_paginas = list(paginator.get_elided_page_range(items_page.number, on_each_side=1, on_ends=1))

    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': items_page.number,
            'has_next': items_page.has_next(),
            'has_previous': items_page.has_previous(),
            'rango_paginas': rango_paginas,  
        }
    }, safe=False)


@login_required
def api_empleado_objetivos(request, empleado_id):
    """
    API 5: Historial de metas y objetivos individuales asignados.
    """
    rol = request.session.get('rol_actual', request.user.rol)
    if not es_subordinado(request.user, empleado_id, rol):
        return JsonResponse({'error': 'Acceso denegado'}, status=403)

    tipo_filtro = request.GET.get('tipo', 'todos')
    queryset = ObjetivoEmpleado.objects.filter(empleado_id=empleado_id).select_related(
        'objetivo', 'objetivo__departamento', 'cargo'
    ).order_by('-fecha_asignacion')

    if tipo_filtro == 'empleado':
        queryset = queryset.filter(cargo__isnull=True)
    elif tipo_filtro == 'cargo':
        queryset = queryset.filter(cargo__isnull=False)

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    paginator = Paginator(queryset, per_page)

    try:
        items_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        items_page = paginator.page(1)

    data = []
    for item in items_page:
        tipo_label = 'Cargo' if item.cargo_id else 'Empleado'
        
        titulo_final = item.objetivo.titulo if item.objetivo.activo else f"{item.objetivo.titulo} (Inactivo)"
        
        cargo_label = None
        if item.cargo:
            cargo_label = item.cargo.nombre if item.cargo.activo else f"{item.cargo.nombre} (Inactivo)"

        data.append({
            'titulo': titulo_final,
            'descripcion': item.objetivo.descripcion,
            'fecha_asignacion': item.fecha_asignacion.strftime('%d-%m-%Y'),
            'fecha_limite': item.fecha_limite.strftime('%d-%m-%Y') if item.fecha_limite else 'N/A',
            'completado': item.completado,
            'departamento': item.objetivo.departamento.nombre if item.objetivo.departamento else 'Global',
            'tipo': tipo_label,
            'nombre_cargo': cargo_label 
        })

    rango_paginas = list(paginator.get_elided_page_range(items_page.number, on_each_side=1, on_ends=1))

    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': items_page.number,
            'has_next': items_page.has_next(),
            'has_previous': items_page.has_previous(),
            'rango_paginas': rango_paginas,  
        }
    })




@login_required
def api_crear_habilidad_rapida(request):
    """
    API para crear una habilidad desde el perfil del empleado vía AJAX
    y retornarla para actualizar el select de inmediato.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre = data.get('nombre', '').strip()
            descripcion = data.get('descripcion', '').strip()

            if not nombre:
                return JsonResponse({'success': False, 'error': 'El nombre es obligatorio.'}, status=400)

            if Habilidad.objects.filter(nombre__iexact=nombre).exists():
                return JsonResponse({'success': False, 'error': 'Esta habilidad ya existe en el catálogo.'}, status=400)

            nueva_habilidad = Habilidad.objects.create(nombre=nombre, descripcion=descripcion)

            return JsonResponse({
                'success': True,
                'habilidad': {
                    'id': nueva_habilidad.id,
                    'nombre': nueva_habilidad.nombre
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)



@login_required
def asignar_habilidad_view(request, empleado_id):
    if request.method == 'POST':
        empleado = get_object_or_404(Empleado, id=empleado_id)
        habilidad_id = request.POST.get('habilidad')
        
        if habilidad_id:
            habilidad = get_object_or_404(Habilidad, id=habilidad_id, activo=True)            
            relacion_existe = empleado.habilidadempleado_set.filter(habilidad=habilidad).exists()
            
            if not relacion_existe:
                empleado.habilidadempleado_set.create(habilidad=habilidad)
                messages.success(request, f"Habilidad '{habilidad.nombre}' vinculada con éxito.")
            else:
                messages.warning(request, "El empleado ya posee esta habilidad asignada.")
        else:
            messages.error(request, "Debe seleccionar una habilidad válida.")
            
    return redirect('empleado_perfil_detalle', empleado_id=empleado_id)



@login_required
def eliminar_habilidad_empleado_view(request, empleado_id, habilidad_id):
    if request.method == 'POST':
        empleado = get_object_or_404(Empleado, id=empleado_id)
        habilidad_vinculada = empleado.habilidadempleado_set.filter(habilidad_id=habilidad_id).first()
        
        if habilidad_vinculada:
            habilidad_vinculada.delete()
            messages.success(request, "Habilidad removida del perfil correctamente.")
        else:
            messages.error(request, "No se encontró la habilidad en el perfil.")
            
    return redirect('empleado_perfil_detalle', empleado_id=empleado_id)




#############################
## NOMINAS
############
def get_nominas_queryset(request):
    rol_actual = request.session.get('rol_actual', request.user.rol)
    
    queryset = Nomina.objects.select_related('empleado').order_by('-fecha_generacion')
    
    dni = request.GET.get('dni')
    estado = request.GET.get('estado')
    departamento_id = request.GET.get('departamento_id')
    
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if rol_actual in ['jefe', 'gerente']:
        try:
            depto_usuario = request.user.persona.empleado.departamento_actual()
            if depto_usuario:
                queryset = queryset.filter(
                    empleado__empleadocargo__cargo__cargodepartamento__departamento=depto_usuario,
                    empleado__empleadocargo__fecha_fin__isnull=True
                )
            else:
                return Nomina.objects.none()
        except (AttributeError, Empleado.DoesNotExist):
            return Nomina.objects.none()
            
    elif departamento_id:
        queryset = queryset.filter(
            empleado__empleadocargo__cargo__cargodepartamento__departamento__id=departamento_id,
            empleado__empleadocargo__fecha_fin__isnull=True
        )

    if dni:
        queryset = queryset.filter(empleado__dni__icontains=dni)
    if estado:
        queryset = queryset.filter(estado=estado)

    if fecha_desde:
        queryset = queryset.filter(fecha_generacion__gte=fecha_desde)
    if fecha_hasta:
        queryset = queryset.filter(fecha_generacion__lte=fecha_hasta)

    return queryset.distinct()




@login_required
def nominas_detalle_view(request):
    estados = Nomina.ESTADO_CHOICES
    return render(request, 'informes/nominas_detalle.html', {'estados': estados})


@login_required
def api_nominas_detalle(request):
    queryset = get_nominas_queryset(request)
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 12)
    paginator = Paginator(queryset, per_page)

    try:
        nominas_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        nominas_page = paginator.page(1)

    rango_paginas = list(paginator.get_elided_page_range(nominas_page.number, on_each_side=2, on_ends=1))

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
            'rango_paginas': rango_paginas,
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
    rol_actual = request.session.get('rol_actual', request.user.rol)
    
    queryset = EvaluacionEmpleado.objects.select_related(
        'empleado',
        'evaluacion'
    ).order_by('-fecha_registro', 'empleado__apellido')
    
    dni = request.GET.get('dni')
    evaluacion_id = request.GET.get('evaluacion_id')
    
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if rol_actual in ['jefe', 'gerente']:
        try:
            depto_usuario = request.user.persona.empleado.departamento_actual()
            if depto_usuario:
                queryset = queryset.filter(
                    empleado__empleadocargo__cargo__cargodepartamento__departamento=depto_usuario,
                    empleado__empleadocargo__fecha_fin__isnull=True
                )
            else:
                return EvaluacionEmpleado.objects.none()
        except (AttributeError, Empleado.DoesNotExist):
            return EvaluacionEmpleado.objects.none()

    if dni:
        queryset = queryset.filter(empleado__dni__icontains=dni)
    if evaluacion_id:
        queryset = queryset.filter(evaluacion__id=evaluacion_id)

    if fecha_desde and fecha_desde.strip():
        queryset = queryset.filter(fecha_registro__gte=fecha_desde)
    if fecha_hasta and fecha_hasta.strip():
        queryset = queryset.filter(fecha_registro__lte=fecha_hasta)

    return queryset.distinct()



@login_required
def evaluaciones_detalle_view(request):
    return render(request, 'informes/evaluaciones_detalle.html')


@login_required
def api_evaluaciones_detalle(request):
    queryset = get_evaluaciones_queryset(request)
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 12)
    paginator = Paginator(queryset, per_page)

    try:
        evaluaciones_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        evaluaciones_page = paginator.page(1)

    rango_paginas = list(paginator.get_elided_page_range(
        evaluaciones_page.number, 
        on_each_side=2, 
        on_ends=1
    ))

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
            'rango_paginas': rango_paginas,
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




## CAPACITACIONES
##################
@login_required
def api_capacitaciones_list(request):
    cursos = Capacitacion.objects.filter(activo=True).order_by('-fecha_inicio').values('id', 'nombre', 'fecha_inicio')
    data = []
    for curso in cursos:
        fecha_str = curso['fecha_inicio'].strftime('%Y-%m-%d') if curso['fecha_inicio'] else "S/F"
        data.append({
            'id': curso['id'],
            'nombre': f"{curso['nombre']} ({fecha_str})"
        })
    return JsonResponse(data, safe=False)



def get_capacitaciones_queryset(request):
    rol_actual = request.session.get('rol_actual', request.user.rol)
    
    queryset = CapacitacionEmpleado.objects.select_related(
        'empleado', 
        'capacitacion'
    ).order_by('-fecha_inscripcion', 'empleado__apellido')
    
    dni = request.GET.get('dni')
    curso_id = request.GET.get('curso_id')
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')

    if rol_actual in ['jefe', 'gerente']:
        try:
            depto_usuario = request.user.persona.empleado.departamento_actual()
            if depto_usuario:
                queryset = queryset.filter(
                    empleado__empleadocargo__cargo__cargodepartamento__departamento=depto_usuario,
                    empleado__empleadocargo__fecha_fin__isnull=True
                )
            else:
                return CapacitacionEmpleado.objects.none()
        except (AttributeError, Empleado.DoesNotExist):
            return CapacitacionEmpleado.objects.none()

    if dni:
        queryset = queryset.filter(empleado__dni__icontains=dni)
    if curso_id:
        queryset = queryset.filter(capacitacion__id=curso_id)
    if estado:
        queryset = queryset.filter(estado=estado)
    if tipo == 'interna':
        queryset = queryset.filter(capacitacion__es_externo=False)
    elif tipo == 'externa':
        queryset = queryset.filter(capacitacion__es_externo=True)

    return queryset.distinct()



@login_required
def capacitaciones_detalle_view(request):
    return render(request, 'informes/capacitaciones_detalle.html')


@login_required
def api_capacitaciones_detalle(request):
    queryset = get_capacitaciones_queryset(request)
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    paginator = Paginator(queryset, per_page)

    try:
        capacitaciones_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        capacitaciones_page = paginator.page(1)

    data = []
    for cap_emp in capacitaciones_page:
        url_perfil = reverse('empleado_perfil_detalle', args=[cap_emp.empleado.id])
        
        data.append({
            'id': cap_emp.id,
            'nombre_completo': f"{cap_emp.empleado.nombre} {cap_emp.empleado.apellido}",
            'dni': cap_emp.empleado.dni,
            'curso_nombre': cap_emp.capacitacion.nombre,
            'es_externo': cap_emp.capacitacion.es_externo,
            'estado': cap_emp.get_estado_display(),
            'estado_raw': cap_emp.estado,
            'fecha_inscripcion': cap_emp.fecha_inscripcion.strftime('%d-%m-%Y'),
            'tiene_certificado': bool(cap_emp.comprobante),
            'url_perfil': url_perfil
        })
    
    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': capacitaciones_page.number,
            'has_next': capacitaciones_page.has_next(),
            'has_previous': capacitaciones_page.has_previous(),
        }
    }, safe=False)


@login_required
def exportar_capacitaciones_csv(request):
    queryset = get_capacitaciones_queryset(request)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="capacitaciones_filtradas.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Empleado', 'DNI', 'Curso', 'Tipo', 'Estado', 'Fecha Inscripción'])
    
    for cap_emp in queryset:
        tipo = "Externa" if cap_emp.capacitacion.es_externo else "Interna"
        writer.writerow([
            f"{cap_emp.empleado.nombre} {cap_emp.empleado.apellido}",
            cap_emp.empleado.dni,
            cap_emp.capacitacion.nombre,
            tipo,
            cap_emp.get_estado_display(),
            cap_emp.fecha_inscripcion.strftime('%d-%m-%Y'),
        ])
    return response



########### OBJETIVOS #########
######################
def get_objetivos_queryset(request):
    rol_actual = request.session.get('rol_actual', request.user.rol)
    
    queryset = ObjetivoEmpleado.objects.select_related(
        'empleado', 
        'objetivo', 
        'cargo'
    ).order_by('-fecha_asignacion', '-id')
    
    dni = request.GET.get('dni')
    completado = request.GET.get('completado') 
    departamento_id = request.GET.get('departamento_id')
    tipo_recurrencia = request.GET.get('tipo_recurrencia')
    
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if rol_actual in ['jefe', 'gerente']:
        try:
            depto_usuario = request.user.persona.empleado.departamento_actual()
            if depto_usuario:
                queryset = queryset.filter(
                    empleado__empleadocargo__fecha_fin__isnull=True,
                    empleado__empleadocargo__cargo__cargodepartamento__departamento=depto_usuario
                )
            else:
                return ObjetivoEmpleado.objects.none()
        except (AttributeError, Empleado.DoesNotExist):
            return ObjetivoEmpleado.objects.none()
            
    elif departamento_id and departamento_id.strip():
        queryset = queryset.filter(
            empleado__empleadocargo__fecha_fin__isnull=True,
            empleado__empleadocargo__cargo__cargodepartamento__departamento_id=departamento_id
        )

    if dni:
        queryset = queryset.filter(empleado__dni__icontains=dni)
    
    if completado != '' and completado is not None:
        valor_bool = True if completado.lower() == 'true' else False
        queryset = queryset.filter(completado=valor_bool)

    if tipo_recurrencia == 'recurrente':
        queryset = queryset.filter(objetivo__es_recurrente=True)
    elif tipo_recurrencia == 'aislado':
        queryset = queryset.filter(objetivo__es_recurrente=False)

    if fecha_desde:
        queryset = queryset.filter(
            (Q(objetivo__es_recurrente=False) & Q(fecha_limite__gte=fecha_desde)) |
            (Q(objetivo__es_recurrente=True) & Q(fecha_asignacion__gte=fecha_desde))
        )
        
    if fecha_hasta:
        queryset = queryset.filter(
            (Q(objetivo__es_recurrente=False) & Q(fecha_limite__lte=fecha_hasta)) |
            (Q(objetivo__es_recurrente=True) & Q(fecha_asignacion__lte=fecha_hasta))
        )

    return queryset.distinct()




@login_required
def objetivos_detalle_view(request):
    rol_actual = request.session.get('rol_actual', request.user.rol)
    
    if rol_actual in ['jefe', 'gerente']:
        try:
            depto = request.user.persona.empleado.departamento_actual()
            departamentos = Departamento.objects.filter(id=depto.id) if depto else Departamento.objects.none()
        except (AttributeError, Empleado.DoesNotExist):
            departamentos = Departamento.objects.none()
    else:
        departamentos = Departamento.objects.all().order_by('nombre')

    return render(request, 'informes/objetivos_detalle.html', {
        'departamentos': departamentos
    })



@login_required
def api_objetivos_detalle(request):
    queryset = get_objetivos_queryset(request)
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 12)
    paginator = Paginator(queryset, per_page)

    try:
        objs_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        objs_page = paginator.page(1)

    rango_paginas = list(paginator.get_elided_page_range(
        objs_page.number, 
        on_each_side=2, 
        on_ends=1
    ))

    data = []
    for rel in objs_page:
        cargo_nombre = rel.cargo.nombre if rel.cargo else "Asignación Manual"        
        f_asignacion = rel.fecha_asignacion.strftime('%d-%m-%Y') if rel.fecha_asignacion else "N/A"

        if rel.objetivo.es_recurrente:
            f_limite = f_asignacion
        else:
            f_limite = rel.fecha_limite.strftime('%d-%m-%Y') if rel.fecha_limite else "Sin fecha"

        nombre_dep = 'General'
        cargo_activo = rel.empleado.empleadocargo_set.filter(fecha_fin__isnull=True).first()
        if cargo_activo:
            rel_depto = cargo_activo.cargo.cargodepartamento_set.first()
            if rel_depto:
                nombre_dep = rel_depto.departamento.nombre

        data.append({
            'id': rel.id,
            'empleado': f"{rel.empleado.nombre} {rel.empleado.apellido}",
            'dni': rel.empleado.dni,
            'objetivo_titulo': rel.objetivo.titulo,
            'objetivo_descripcion': rel.objetivo.descripcion,
            'es_recurrente': rel.objetivo.es_recurrente, 
            'departamento': nombre_dep,
            'cargo_nombre': cargo_nombre,
            'fecha_asignacion': f_asignacion,
            'fecha_limite': f_limite, 
            'completado': rel.completado,
            'url_perfil': reverse('empleado_perfil_detalle', args=[rel.empleado.id]),
        })
    
    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': objs_page.number,
            'has_next': objs_page.has_next(),
            'has_previous': objs_page.has_previous(),
            'rango_paginas': rango_paginas,
        }
    })



@login_required
def exportar_objetivos_csv(request):
    queryset = get_objetivos_queryset(request)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_objetivos.csv"'
    
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    
    writer.writerow([
        'Empleado', 'DNI', 'Objetivo', 'Tipo', 'Departamento', 
        'Cargo en Asignación', 'Fecha Asignación', 'Fecha Límite', 'Estado'
    ])
    
    for rel in queryset:
        tipo = "Recurrente (Diario)" if rel.objetivo.es_recurrente else "Aislado (Único)"
        
        if rel.objetivo.es_recurrente:
            f_limite = rel.fecha_asignacion
        else:
            f_limite = rel.fecha_limite if rel.fecha_limite else 'Sin límite'
            
        estado = "Completado" if rel.completado else "Pendiente"
        
        nombre_dep = 'General'
        if rel.cargo:
            rel_depto = rel.cargo.cargodepartamento_set.first()
            if rel_depto:
                nombre_dep = rel_depto.departamento.nombre
        else:
            cargo_activo = rel.empleado.empleadocargo_set.filter(fecha_fin__isnull=True).first()
            if cargo_activo:
                rel_depto = cargo_activo.cargo.cargodepartamento_set.first()
                if rel_depto:
                    nombre_dep = rel_depto.departamento.nombre
        
        writer.writerow([
            f"{rel.empleado.nombre} {rel.empleado.apellido}",
            rel.empleado.dni,
            rel.objetivo.titulo,
            tipo,
            nombre_dep,
            rel.cargo.nombre if rel.cargo else "Manual",
            rel.fecha_asignacion,
            f_limite,  
            estado
        ])
        
    return response




##############################################
            ## VISTA EMPLEADO ##
##############################################
@login_required
def objetivos_detalle_view_emp(request):
    return render(request, 'informes_vista_empleado/objetivos_detalle.html')


@login_required
def api_objetivos_detalle_emp(request):
    
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
    per_page = request.GET.get('per_page', 13) 
    
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
def asistencias_detalle_view_emp(request):
    return render(request, 'informes_vista_empleado/asistencias_detalle.html')


@login_required
def api_asistencias_detalle_emp(request):
    empleado = None
    try:
        empleado = request.user.persona.empleado 
    except AttributeError:
        pass 
    
    if not empleado:
         return JsonResponse({'results': [], 'pagination': {'total_pages': 0, 'current_page': 1, 'has_next': False, 'has_previous': False,}}, safe=False)

    queryset = HistorialAsistencia.objects.filter(empleado=empleado).order_by('-fecha_asistencia', '-hora_entrada')

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 15) 
    paginator = Paginator(queryset, per_page)

    try:
        asistencias_page = paginator.page(page)
    except PageNotAnInteger:
        asistencias_page = paginator.page(1)
    except EmptyPage:
        asistencias_page = paginator.page(paginator.num_pages)
    
    data = []
    for asistencia in asistencias_page:
        entrada_txt = "Licencia" if asistencia.licencia else (asistencia.hora_entrada.strftime('%H:%M') if asistencia.hora_entrada else None)
        salida_txt = "Licencia" if asistencia.licencia else (asistencia.hora_salida.strftime('%H:%M') if asistencia.hora_salida else None)

        data.append({
            'fecha_asistencia': asistencia.fecha_asistencia.strftime('%Y-%m-%d'),
            'hora_entrada': entrada_txt,
            'hora_salida': salida_txt,
            'confirmado': asistencia.confirmado,
            'tardanza': asistencia.tardanza,
            'es_licencia': asistencia.licencia, 
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
def evaluaciones_detalle_view_emp(request):
    return render(request, 'informes_vista_empleado/evaluaciones_detalle.html')

@login_required
def api_evaluaciones_detalle_emp(request):
    empleado = None
    try:
        empleado = request.user.persona.empleado 
    except AttributeError:
        pass 
    
    if not empleado:
         return JsonResponse({'results': [], 'pagination': {'total_pages': 0, 'current_page': 1, 'has_next': False, 'has_previous': False,}}, safe=False)

    queryset = EvaluacionEmpleado.objects.filter(empleado=empleado).order_by('-fecha_registro')

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 15) 
    paginator = Paginator(queryset, per_page)

    try:
        evaluaciones_page = paginator.page(page)
    except PageNotAnInteger:
        evaluaciones_page = paginator.page(1)
    except EmptyPage:
        evaluaciones_page = paginator.page(paginator.num_pages)
    
    data = []
    for eval_emp in evaluaciones_page:
        data.append({
            'descripcion': eval_emp.evaluacion.descripcion,
            'fecha_registro': eval_emp.fecha_registro.strftime('%Y-%m-%d'),
            'comentarios': eval_emp.comentarios,
            'calificacion_final': str(eval_emp.calificacion_final) if eval_emp.calificacion_final is not None else None,
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
def capacitaciones_detalle_view_emp(request):
    return render(request, 'informes_vista_empleado/capacitaciones_detalle.html')

@login_required
def api_capacitaciones_detalle_emp(request):
    try:
        empleado = request.user.persona.empleado 
    except AttributeError:
        return JsonResponse({'results': [], 'pagination': {'total_pages': 0}}, safe=False)

    queryset = CapacitacionEmpleado.objects.filter(empleado=empleado).select_related('capacitacion').order_by('-fecha_inscripcion')

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 15) 
    paginator = Paginator(queryset, per_page)

    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    data = []
    for cap_emp in page_obj:
        es_externo = cap_emp.capacitacion.es_externo
        
        estado_display = cap_emp.get_estado_display()
        if cap_emp.estado == 'INSCRIPTO':
            estado_display = "Interesado" if es_externo else "Inscripto"

        data.append({
            'curso': cap_emp.capacitacion.nombre,
            'tipo': "Externo" if cap_emp.capacitacion.es_externo else "Interno",
            'es_externo': cap_emp.capacitacion.es_externo,
            'fecha_inscripcion': cap_emp.fecha_inscripcion.strftime('%Y-%m-%d'),
            'fecha_inicio': cap_emp.capacitacion.fecha_inicio.strftime('%Y-%m-%d') if cap_emp.capacitacion.fecha_inicio else None,
            'estado': cap_emp.get_estado_display(),
            'estado_raw': cap_emp.estado,
            'url_curso': cap_emp.capacitacion.url_sitio if cap_emp.capacitacion.es_externo else None,
            'fecha_completado': cap_emp.fecha_completado.strftime('%Y-%m-%d') if cap_emp.fecha_completado else None
        })
    
    return JsonResponse({
        'results': data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    }, safe=False)
