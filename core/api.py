from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Avg, Count
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from datetime import timedelta, date
from django.db.models.functions import ExtractMonth, ExtractYear
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from django.utils import translation
from django.db.models import Q
import calendar

from core.models import (
    Empleado,
    HistorialAsistencia,
    VacacionesSolicitud,
    EvaluacionEmpleado,
    Evaluacion,
    Nomina,
    Departamento,
    Cargo,
    CargoDepartamento,
    EmpleadoCargo,
    Objetivo,
    ObjetivoEmpleado,
    Beneficio,
    BeneficioEmpleadoNomina,
    LogroEmpleado,
    Logro,
    CapacitacionEmpleado,
)

# Helper to force float for Decimal
def to_float(value):
    try:
        return float(value)
    except:
        return 0.0


import locale
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Avg

# Intentar establecer idioma en español para los nombres de meses
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, '')

@require_GET
@login_required
def api_kpis(request):
    today = timezone.localdate()
    
    nombre_mes_actual = today.strftime('%B %Y').capitalize()
    absences_count = HistorialAsistencia.objects.filter(
        fecha_asistencia__month=today.month,
        fecha_asistencia__year=today.year,
        confirmado=False
    ).count()

    ultima_nomina = Nomina.objects.order_by('-fecha_generacion').first()
    
    if ultima_nomina:
        fecha_datos = ultima_nomina.fecha_generacion
        nombre_mes_costo = fecha_datos.strftime('%B %Y').capitalize()
        payroll_cost = Nomina.objects.filter(
            fecha_generacion__month=fecha_datos.month,
            fecha_generacion__year=fecha_datos.year
        ).aggregate(total=Sum('monto_neto'))['total'] or 0
    else:
        nombre_mes_costo = "Sin datos"
        payroll_cost = 0

    start_eval = today - timedelta(days=365)
    rango_eval = f"{start_eval.strftime('%b %Y')} - {today.strftime('%b %Y')}".capitalize()
    
    eval_avg = EvaluacionEmpleado.objects.filter(
        fecha_registro__gte=start_eval,
        empleado__estado='activo'
    ).aggregate(avg=Avg('calificacion_final'))['avg'] or 0

    return JsonResponse({
        "employees_total": Empleado.objects.filter(estado='activo').count(),
        "absences_count": absences_count,
        "absences_month_name": nombre_mes_actual,
        "payroll_cost": float(payroll_cost),
        "payroll_month_name": nombre_mes_costo,
        "eval_avg": float(eval_avg),
        "eval_range": rango_eval
    })



@login_required
def api_vacaciones(request):
    hoy = timezone.now().date()
    periodo_solicitado = request.GET.get('periodo')
    
    periodos_map = {
        '1m': 0, '2m': 2, '3m': 3, '6m': 6, '12m': 12
    }

    def obtener_rango(p_code):
        meses = periodos_map.get(p_code, 0)
        s_date = (hoy - relativedelta(months=meses)).replace(day=1) if meses > 0 else hoy.replace(day=1)
        return s_date, hoy

    if periodo_solicitado:
        start_date, end_date = obtener_rango(periodo_solicitado)
        periodo_final = periodo_solicitado
    
    else:
        periodo_final = '1m' 
        for p_code in ['1m', '2m', '3m', '6m', '12m']:
            sd, ed = obtener_rango(p_code)
            if VacacionesSolicitud.objects.filter(fecha_solicitud__range=[sd, ed]).exists():
                start_date, end_date = sd, ed
                periodo_final = p_code
                break
        else:
            start_date, end_date = obtener_rango('1m')

    qs = VacacionesSolicitud.objects.filter(fecha_solicitud__range=[start_date, end_date])

    return JsonResponse({
        "total": qs.count(),
        "approved": qs.filter(estado='aprobado').count(),
        "pending": qs.filter(estado='pendiente').count(),
        "rejected": qs.filter(estado='rechazado').count(),
        "cancelled": qs.filter(estado='cancelado').count(),
        "start_date_formatted": start_date.strftime('%d %b %Y'),
        "end_date_formatted": end_date.strftime('%d %b %Y'),
        "active_period": periodo_final
    })


@require_GET
@login_required
def api_asistencias(request):
    today = timezone.localdate()
    period = request.GET.get('periodo', '30d') 

    if period == '2m':
        days_back = 60
        group_by = 'week'
    elif period == '3m':
        days_back = 90
        group_by = 'week'
    elif period == '6m':
        days_back = 180
        group_by = 'month'
    elif period == '12m':
        days_back = 365
        group_by = 'month'
    else:
        days_back = 30
        group_by = 'day'
    
    start_date = today - timedelta(days=days_back - 1)

    qs = HistorialAsistencia.objects.filter(fecha_asistencia__gte=start_date, fecha_asistencia__lte=today)
    
    labels = []
    present = []
    ausent = []
    late = []
    
    if group_by == 'day':
        for i in range(days_back):
            d = start_date + timedelta(days=i)
            labels.append(d.strftime('%d %b'))
            day_qs = qs.filter(fecha_asistencia=d)
            present.append(day_qs.filter(confirmado=True).count())
            late.append(day_qs.filter(tardanza=True).count())
            ausent.append(day_qs.filter(confirmado=False).count())
    
    elif group_by == 'month':
        current_date = start_date
        while current_date <= today:
            month_end = current_date + relativedelta(months=1, days=-1)
            month_qs = qs.filter(fecha_asistencia__month=current_date.month, fecha_asistencia__year=current_date.year)
            labels.append(current_date.strftime('%b %Y'))
            present.append(month_qs.filter(confirmado=True).count())
            late.append(month_qs.filter(tardanza=True).count())
            ausent.append(month_qs.filter(confirmado=False).count())
            current_date = month_end + timedelta(days=1)

    elif group_by == 'week':
        current_date = start_date
        
        while current_date <= today:
            week_start = current_date
            week_end = current_date + timedelta(days=6)
            
            if week_end > today:
                week_end = today

            week_qs = qs.filter(fecha_asistencia__range=[week_start, week_end])
            
            start_label = week_start.strftime('%d %b')
            end_label = week_end.strftime('%d %b')

            if start_label == end_label: 
                 labels.append(f"Día {start_label}")
            else:
                 labels.append(f"{start_label} - {end_label}")

            present.append(week_qs.filter(confirmado=True).count())
            late.append(week_qs.filter(tardanza=True).count())
            ausent.append(week_qs.filter(confirmado=False).count())

            current_date = week_end + timedelta(days=1)

            if current_date > today + timedelta(days=7): 
                break
            
    start_date_formatted = start_date.strftime('%d %b %Y')
    end_date_formatted = today.strftime('%d %b %Y')

    return JsonResponse({
        "labels": labels, 
        "present": present, 
        "late": late, 
        "ausent": ausent,
        "start_date_formatted": start_date_formatted,
        "end_date_formatted": end_date_formatted,
    })




@require_GET
@login_required
def api_evaluaciones(request):
    today = timezone.localdate()

    period = request.GET.get('periodo', '12m') 
    
    if period == '3m':
        start_date = today + relativedelta(months=-3)
    elif period == '6m':
        start_date = today + relativedelta(months=-6)
    elif period == '24m':
        start_date = today + relativedelta(years=-2)
    else:
        start_date = today + relativedelta(years=-1) 

    counts = [0,0,0,0,0,0,0,0,0,0]
    evals = EvaluacionEmpleado.objects.exclude(calificacion_final__isnull=True).filter(
        fecha_registro__gte=start_date).values_list('calificacion_final', flat=True)
    for v in evals:
        try:
            i = int(round(float(v)))
            if 1 <= i <= 10:
                counts[i-1] += 1
        except:
            continue

    start_date_formatted = start_date.strftime('%b %Y')
    end_date_formatted = today.strftime('%b %Y')

    return JsonResponse({
        "labels": ["1","2","3","4","5","6","7","8","9","10"], 
        "counts": counts,
        "start_date_formatted": start_date_formatted,
        "end_date_formatted": end_date_formatted,
        })





@require_GET
@login_required
def api_nominas(request):
    ultima_nomina = Nomina.objects.order_by('-fecha_generacion').first()
    
    if not ultima_nomina:
        return JsonResponse({
            "base": 0, "benefits": 0, "discounts": 0, "extras": 0,
            "start_date_formatted": "Sin datos", "end_date_formatted": ""
        })

    ultimo_mes_con_datos = ultima_nomina.fecha_generacion.replace(day=1)
    period = request.GET.get('periodo', '1m') 
    num_months = int(period.replace('m', ''))
    
    end_date = ultimo_mes_con_datos + relativedelta(months=+1, days=-1)
    start_date = ultimo_mes_con_datos - relativedelta(months=(num_months - 1))

    qs = Nomina.objects.filter(fecha_generacion__gte=start_date, fecha_generacion__lte=end_date)

    start_date_formatted = start_date.strftime('%b. %Y').capitalize()
    end_date_formatted = end_date.strftime('%b. %Y').capitalize()

    base = qs.aggregate(total=Sum('monto_bruto'))['total'] or 0
    benefits = qs.aggregate(total=Sum('total_beneficios'))['total'] or 0
    discounts = qs.aggregate(total=Sum('total_descuentos'))['total'] or 0
    extras = qs.aggregate(total=Sum('monto_extra_pactado'))['total'] or 0
    
    return JsonResponse({
        "base": float(base - extras),
        "benefits": float(benefits),
        "discounts": float(discounts),
        "extras": float(extras),
        "start_date_formatted": start_date_formatted,
        "end_date_formatted": end_date_formatted if num_months > 1 else start_date_formatted,
    })



@require_GET
@login_required
def api_labor_cost_comparison(request):
    today = timezone.localdate()
    year1 = int(request.GET.get('year1', today.year - 1))
    year2 = int(request.GET.get('year2', today.year))

    def get_monthly_costs(year):
        costs = Nomina.objects.filter(
            fecha_generacion__year=year
        ).annotate(
            month=ExtractMonth('fecha_generacion')
        ).values('month').annotate(
            total_cost=Sum('monto_neto')
        ).order_by('month')
        
        monthly_data = {item['month']: float(item['total_cost'] or 0) for item in costs}
        
        full_year_data = [monthly_data.get(month, 0) for month in range(1, 13)]
        return full_year_data

    data_year1 = get_monthly_costs(year1)
    data_year2 = get_monthly_costs(year2)
    
    months_labels = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    return JsonResponse({
        "labels": months_labels,
        "year1_label": str(year1),
        "year2_label": str(year2),
        "data_year1": data_year1,
        "data_year2": data_year2,
    })



@require_GET
@login_required
def api_estructura(request):
    depts = Departamento.objects.all()
    labels = []
    counts = []
    for d in depts:
        cargos_ids = CargoDepartamento.objects.filter(departamento=d).values_list('cargo_id', flat=True)
        emp_count = EmpleadoCargo.objects.filter(cargo_id__in=cargos_ids, fecha_fin__isnull=True).values('empleado').distinct().count()
        labels.append(d.nombre)
        counts.append(emp_count)
    return JsonResponse({"labels": labels, "counts": counts})




@require_GET
@login_required
def api_objetivos(request):
    department_id = request.GET.get('departamento_id')

    items = []
    objs_queryset = Objetivo.objects.filter(activo=True).select_related('departamento', 'creado_por__persona').order_by('-fecha_creacion')

    if department_id and department_id != 'todos':
        try:
            objs_queryset = objs_queryset.filter(departamento__id=int(department_id))
        except ValueError:
            pass 
            
    objs = objs_queryset[:50] 

    for o in objs:
        asignaciones = ObjetivoEmpleado.objects.filter(objetivo=o)
        
        if asignaciones.exists():
            total_asignados = asignaciones.count()
            completados = asignaciones.filter(completado=True).count()
            avg_progress = (completados * 100) // total_asignados
            
            tiene_cargo = asignaciones.filter(cargo__isnull=False).exists()
            tipo_label = "Por Cargo" if tiene_cargo else "Directo"
        else:
            avg_progress = 0
            tipo_label = "Sin asignar"

        if o.departamento:
            owner_name = o.departamento.nombre
        elif o.creado_por and hasattr(o.creado_por, 'persona'):
            owner_name = f"{o.creado_por.persona.nombre} {o.creado_por.persona.apellido}"
        else:
            owner_name = o.creado_por.username if o.creado_por else "Sistema"

        items.append({
            "title": o.titulo,
            "type": f"{'Recurrente' if o.es_recurrente else 'Único'} ({tipo_label})",
            "owner": owner_name,
            "progress": int(avg_progress)
        })

    return JsonResponse({"items": items})




@require_GET
@login_required
def api_capacitaciones(request):
    today = timezone.localdate()
    period = request.GET.get('periodo', '6m') 
    
    try:
        num_months = int(period.replace('m', ''))
    except ValueError:
        num_months = 6

    start_date = (today.replace(day=1) - relativedelta(months=num_months - 1))
    
    qs = CapacitacionEmpleado.objects.filter(
        fecha_inscripcion__gte=start_date, 
        fecha_inscripcion__lte=today
    )

    labels, internas, externas = [], [], []

    current_date = start_date
    while current_date <= today:
        month_qs = qs.filter(
            fecha_inscripcion__month=current_date.month, 
            fecha_inscripcion__year=current_date.year
        )
        
        labels.append(current_date.strftime('%b %y').capitalize())
        internas.append(month_qs.filter(capacitacion__es_externo=False).count())
        externas.append(month_qs.filter(capacitacion__es_externo=True).count())
        
        current_date += relativedelta(months=1)

    return JsonResponse({
        "labels": labels,
        "internas": internas,
        "externas": externas,
        "start_date_formatted": start_date.strftime('%d %b %Y'),
        "end_date_formatted": today.strftime('%d %b %Y'),
    })


###########################################################
###########################################################
###########################################################
###########################################################
###########################################################
###########################################################
                # DASHBOARD EMPLEADO #
###########################################################
###########################################################
###########################################################
###########################################################
###########################################################

@login_required
def api_dashboard_empleado(request):
    persona = getattr(request.user, 'persona', None)
    
    if not persona:
        return JsonResponse({'error': 'Perfil incompleto'}, status=403)
    empleado = Empleado.objects.get(id=persona.id)
    hoy = timezone.localtime(timezone.now()).date()
    
    qs = ObjetivoEmpleado.objects.filter(empleado=empleado, objetivo__activo=True).select_related('objetivo')
    qs_diarios = qs.filter(objetivo__es_recurrente=True, fecha_asignacion=hoy)
    qs_cargo_vigentes = qs.filter(objetivo__es_recurrente=False).filter(
        Q(fecha_limite__gte=hoy) | Q(fecha_limite__isnull=True)
    )

    with translation.override('es'):
        fecha_str = hoy.strftime("%A, %d de %B %Y").capitalize()

    data = {
        "fecha_formateada": fecha_str,
        "diarios": [
            {"id": o.id, "titulo": o.objetivo.titulo, "descripcion": o.objetivo.descripcion, "completado": o.completado} 
            for o in qs_diarios
        ],
        "cargo": [
            {
                "id": o.id, "titulo": o.objetivo.titulo, "completado": o.completado,
                "descripcion": o.objetivo.descripcion,
                "fecha_completa": o.fecha_limite.isoformat() if o.fecha_limite else None, 
                "vence": o.fecha_limite.strftime("%d/%m/%Y") if o.fecha_limite else None,
                "atrasado": o.fecha_limite < hoy if o.fecha_limite else False,
                "es_hoy": o.fecha_limite == hoy if o.fecha_limite else False 
            } for o in qs_cargo_vigentes
        ]   
    }
    return JsonResponse(data)



@require_GET
@login_required
def api_asistencia_empleado(request):
    persona = getattr(request.user, 'persona', None)
    if not persona:
        return JsonResponse({'error': 'Perfil incompleto'}, status=403)
    empleado = Empleado.objects.get(id=persona.id)
    
    hoy = timezone.localtime(timezone.now()).date() 
    primer_dia_mes = hoy.replace(day=1)
    
    total_dias_laborables_contados = 0
    dias_asistidos = 0

    current_day = primer_dia_mes
    while current_day <= hoy:
        if current_day.weekday() not in [5, 6]: 
            total_dias_laborables_contados += 1
            
            asistencia_del_dia = HistorialAsistencia.objects.filter(
                empleado=empleado,
                fecha_asistencia=current_day,
                confirmado=True
            ).exists()

            if asistencia_del_dia:
                dias_asistidos += 1
                
        current_day += timedelta(days=1)

    porcentaje_asistencia = (dias_asistidos / total_dias_laborables_contados * 100) if total_dias_laborables_contados > 0 else 0

    
    registro_hoy = HistorialAsistencia.objects.filter(empleado=empleado, fecha_asistencia=hoy).first()

    estado_hoy = "Nada marcado"
    if registro_hoy:
        if registro_hoy.hora_entrada and not registro_hoy.hora_salida:
            estado_hoy = "Entrada marcada"
        elif registro_hoy.hora_entrada and registro_hoy.hora_salida:
            estado_hoy = "Ambos marcados"


    return JsonResponse({
        "asistencia_mes": round(porcentaje_asistencia, 1),
        "estado_hoy": estado_hoy,
    })



@require_GET
@login_required
def api_evaluaciones_empleado(request):
    persona = getattr(request.user, 'persona', None)
    if not persona:
        return JsonResponse({'error': 'Perfil incompleto'}, status=403)
    empleado = Empleado.objects.get(id=persona.id)

    hoy = timezone.localtime(timezone.now()).date() 
    hace_un_año = hoy - timedelta(days=365)
    
    promedio_evaluaciones = EvaluacionEmpleado.objects.filter(
        empleado=empleado,
        fecha_registro__gte=hace_un_año
    ).aggregate(
        promedio=Avg('calificacion_final')
    )['promedio']

    evaluaciones_pendientes_qs = EvaluacionEmpleado.objects.filter(
        empleado=empleado,
        calificacion_final__isnull=True,
    ).order_by('-fecha_registro')

    lista_pendientes = [
        {
            'id': ev.id,
            'titulo': str(ev.evaluacion),
            'fecha_registro': ev.fecha_registro.strftime('%d/%m/%Y'),
        }
        for ev in evaluaciones_pendientes_qs
    ]

    return JsonResponse({
        "promedio_evaluaciones": round(float(promedio_evaluaciones), 2) if promedio_evaluaciones is not None else None,
        "pendientes": lista_pendientes
    })




@require_GET
@login_required
def api_beneficios_empleado(request):
    persona = getattr(request.user, 'persona', None)
    if not persona:
        return JsonResponse({'error': 'Perfil incompleto'}, status=403)
    empleado = Empleado.objects.get(id=persona.id)

    beneficios_asignados_ids = BeneficioEmpleadoNomina.objects.filter(empleado=empleado).values_list('beneficio_id', flat=True)

    beneficios_asignados = Beneficio.objects.filter(id__in=beneficios_asignados_ids)
    
    lista_asignados = [
        {
            'id': b.id,
            'descripcion': b.descripcion,
            'valor': f"${b.monto}" if b.monto else f"{b.porcentaje}%",
            'fijo': b.fijo
        }
        for b in beneficios_asignados
    ]

    beneficios_potenciales = Beneficio.objects.filter(
        activo=True
    ).exclude(
        Q(id__in=beneficios_asignados_ids) | Q(fijo=True)
    )

    lista_potenciales = [
        {
            'id': b.id,
            'descripcion': b.descripcion,
            'valor': f"${b.monto}" if b.monto else f"{b.porcentaje}%"
        }
        for b in beneficios_potenciales
    ]
    
    return JsonResponse({
        "asignados": lista_asignados,
        "potenciales": lista_potenciales,
    })




@require_GET
@login_required
def api_logros_empleado(request):
    persona = getattr(request.user, 'persona', None)
    if not persona:
        return JsonResponse({'error': 'Perfil incompleto'}, status=403)
    
    try:
        empleado = Empleado.objects.get(id=persona.id)
    except Empleado.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado'}, status=404)

    todos_los_logros = Logro.objects.all()
    
    logros_del_empleado = {le.logro_id: le for le in LogroEmpleado.objects.filter(empleado=empleado)}

    anios_map = {
        'ANTIGUEDAD_1': '1 año', 'ANTIGUEDAD_3': '3 años', 'ANTIGUEDAD_5': '5 años',
        'ANTIGUEDAD_10': '10 años', 'ANTIGUEDAD_15': '15 años', 'ANTIGUEDAD_20': '20 años',
        'ANTIGUEDAD_25': '25 años', 'ANTIGUEDAD_30': '30 años', 'ANTIGUEDAD_40': '40 años'
    }

    lista_logros = []
    
    for logro in todos_los_logros:
        registro_usuario = logros_del_empleado.get(logro.id)
        
        tipo = logro.tipo
        requisito_texto = ""

        if tipo == 'ASISTENCIA_PERFECTA':
            requisito_texto = "100% de asistencia en el mes (Lun-Vie, sin feriados)."
        elif tipo in anios_map:
            requisito_texto = f"Haber cumplido {anios_map[tipo]} de antigüedad total en la empresa."
        else:
            requisito_texto = "Consultar los requisitos con el área de RRHH."

        lista_logros.append({
            'id': logro.id,
            'titulo': logro.descripcion,
            'completado': registro_usuario.completado if registro_usuario else False,
            'fecha_asignacion': registro_usuario.fecha_asignacion.strftime('%d/%m/%Y') if (registro_usuario and registro_usuario.fecha_asignacion) else None,
            'tipo': tipo,
            'requisito': requisito_texto
        })
    
    lista_logros.sort(key=lambda x: (not x['completado'], x['titulo']))

    return JsonResponse({
        "logros": lista_logros,
    })




@login_required
@require_GET
def api_capacitaciones_empleado(request):
    try:
        empleado = request.user.persona.empleado 
    except AttributeError:
        return JsonResponse({'error': 'Perfil incompleto'}, status=403)

    capacitaciones_activas = CapacitacionEmpleado.objects.filter(
        empleado=empleado
    ).exclude(
        estado__in=['COMPLETADO', 'CANCELADO']
    ).select_related('capacitacion').order_by('capacitacion__fecha_inicio')

    lista_capacitaciones = []
    for cap in capacitaciones_activas:
        es_externo = cap.capacitacion.es_externo
        
        estado_display = cap.get_estado_display()
        if cap.estado == 'INSCRIPTO':
            estado_display = "Interesado" if es_externo else "Inscripto"

        lista_capacitaciones.append({
            'id': cap.id,
            'titulo': cap.capacitacion.nombre,
            'fecha_inicio': cap.capacitacion.fecha_inicio.strftime('%d/%m/%Y') if cap.capacitacion.fecha_inicio else None,
            'estado': estado_display,
            'es_externo': es_externo,
            'url_curso': cap.capacitacion.url_sitio if es_externo else None,
        })

    return JsonResponse({
        "mis_capacitaciones": lista_capacitaciones
    })
