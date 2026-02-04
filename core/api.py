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
)

# Helper to force float for Decimal
def to_float(value):
    try:
        return float(value)
    except:
        return 0.0


@require_GET
@login_required
def api_kpis(request):
    today = timezone.localdate()

    first_day_of_current_month = today.replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_previous_month = last_day_of_previous_month.replace(day=1)

    start_date_payroll = first_day_of_previous_month
    end_date_payroll = last_day_of_previous_month

    start_date_evaluations = today - timedelta(days=365) 

    employees_total = Empleado.objects.count()
    absences_month = HistorialAsistencia.objects.filter(
        fecha_asistencia__gte=start_date_payroll, 
        fecha_asistencia__lte=end_date_payroll,
        confirmado=False
        ).count()
    payroll_cost_month = Nomina.objects.filter(
        fecha_generacion__gte=start_date_payroll,
        fecha_generacion__lte=end_date_payroll,
        ).aggregate(total=Sum('monto_neto'))['total'] or 0

    eval_avg = EvaluacionEmpleado.objects.filter(fecha_registro__gte=start_date_evaluations
                                                 ).aggregate(avg=Avg('calificacion_final'))['avg'] or 0  

    return JsonResponse({
        "employees_total": employees_total,
        "absences_month": absences_month,
        "payroll_cost_month": to_float(payroll_cost_month),
        "eval_avg": float(eval_avg)
    })


@require_GET
@login_required
def api_vacaciones(request):
    today = timezone.localdate()

    period = request.GET.get('periodo', '1m') 
    
    start_date = today.replace(day=1)

    if period == '2m':
        start_date = today + relativedelta(months=-1, day=1)
    elif period == '3m':
        start_date = today + relativedelta(months=-3, day=1)
    elif period == '6m':
        start_date = today + relativedelta(months=-6, day=1)
    elif period == '12m':
        start_date = today + relativedelta(years=-1, day=1)
    elif period == '24m':
        start_date = today + relativedelta(years=-2, day=1)
    
    qs = VacacionesSolicitud.objects.filter(fecha_solicitud__gte=start_date)

    start_date_formatted = start_date.strftime('%d %b %Y')
    end_date_formatted = today.strftime('%d %b %Y')

    approved = qs.filter(estado__iexact='aprobado').count()
    pending = qs.filter(estado__iexact='pendiente').count()
    rejected = qs.filter(estado__iexact='rechazado').count()
    cancelled = qs.filter(estado__iexact='cancelado').count()

    return JsonResponse({
        "total": qs.count(),
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "cancelled": cancelled,
        "start_date_formatted": start_date_formatted,
        "end_date_formatted": end_date_formatted,
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
    today = timezone.localdate()
    current_month_start = today.replace(day=1)
    period = request.GET.get('periodo', '1m') 
    
    ultima_nomina = Nomina.objects.order_by('-fecha_generacion').first()

    if ultima_nomina and ultima_nomina.fecha_generacion >= current_month_start:
        end_date = today.replace(day=1) + relativedelta(months=+1, days=-1)
        months_to_go_back = 1 
    else:
        end_date = current_month_start + relativedelta(days=-1) 
        months_to_go_back = 0 


    num_months = int(period.replace('m', ''))
    
    start_date = (end_date + relativedelta(day=1)) + relativedelta(months=-(num_months - 1))

    qs = Nomina.objects.filter(fecha_generacion__gte=start_date, fecha_generacion__lte=end_date)

    start_date_formatted = start_date.strftime('%b. %Y').capitalize()
    end_date_formatted = end_date.strftime('%b. %Y').capitalize()

    if period == '1m':
        range_display_end = start_date_formatted
    else:
        range_display_end = end_date_formatted

    base = qs.aggregate(total=Sum('monto_bruto'))['total'] or 0
    benefits = qs.aggregate(total=Sum('total_beneficios'))['total'] or 0
    discounts = qs.aggregate(total=Sum('total_descuentos'))['total'] or 0
    extras = qs.aggregate(total=Sum('monto_extra_pactado'))['total'] or 0
    state_counts_qs = qs.values('estado').annotate(count=Count('id'))
    state_counts = {item['estado']: item['count'] for item in state_counts_qs}
    return JsonResponse({
        "base": to_float(base-extras),
        "benefits": to_float(benefits),
        "discounts": to_float(discounts),
        "extras": to_float(extras),
        "state_counts": state_counts,
        "start_date_formatted": start_date_formatted,
        "end_date_formatted": range_display_end,
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
    
    months_labels = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

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
        "promedio_evaluaciones": round(float(promedio_evaluaciones), 2) if promedio_evaluaciones is not None else 'N/A',
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
    empleado = Empleado.objects.get(id=persona.id)

    logros_empleado_qs = LogroEmpleado.objects.filter(
        empleado=empleado
    ).order_by('completado', '-fecha_asignacion')

    lista_logros = []
    for le in logros_empleado_qs:
        requisito_texto = "" 
        if le.logro.tipo == 'ASISTENCIA_PERFECTA':
            requisito_texto = "100% de asistencia en el mes (Lun-Vie, sin feriados)."
        else:
            requisito_texto = "Verificar requisitos con RRHH."

        lista_logros.append({
            'id': le.id,
            'titulo': le.logro.descripcion,
            'completado': le.completado,
            'fecha_asignacion': le.fecha_asignacion.strftime('%d/%m/%Y') if le.fecha_asignacion else None,
            'tipo': le.logro.tipo,
            'requisito': requisito_texto
        })
    
    return JsonResponse({
        "logros": lista_logros,
    })
