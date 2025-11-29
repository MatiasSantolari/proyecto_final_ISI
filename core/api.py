from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Avg, Count
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta

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
    ObjetivoCargo
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
    first_day = today.replace(day=1)
    start_date = today - timedelta(days=365) 

    employees_total = Empleado.objects.count()
    absences_month = HistorialAsistencia.objects.filter(fecha_asistencia__gte=first_day, confirmado=False).count()
    payroll_cost_month = Nomina.objects.filter(fecha_generacion__gte=first_day).aggregate(total=Sum('monto_neto'))['total'] or 0

    eval_avg = EvaluacionEmpleado.objects.filter(fecha_registro__gte=start_date
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

    if period == '3m':
        start_date = today + relativedelta(months=-3, day=1)
    elif period == '6m':
        start_date = today + relativedelta(months=-6, day=1)
    elif period == '12m':
        start_date = today + relativedelta(years=-1, day=1)
    elif period == '24m':
        start_date = today + relativedelta(years=-2, day=1)
    
    qs = VacacionesSolicitud.objects.filter(fecha_solicitud__gte=start_date)

    approved = qs.filter(estado__iexact='aprobado').count()
    pending = qs.filter(estado__iexact='pendiente').count()
    rejected = qs.filter(estado__iexact='rechazado').count()
    cancelled = qs.filter(estado__iexact='cancelado').count()

    return JsonResponse({
        "total": qs.count(),
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "cancelled": cancelled
    })


@require_GET
@login_required
def api_asistencias(request):
    today = timezone.localdate()
    period = request.GET.get('periodo', '30d') 

    if period == '3m':
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
    objs_queryset = Objetivo.objects.filter(activo=True).order_by('-fecha_creacion')

    if department_id and department_id != 'todos':
        try:
            objs_queryset = objs_queryset.filter(departamento__id=int(department_id))
        except ValueError:
            pass 
    objs = objs_queryset[:50] 

    for o in objs:
        emps = ObjetivoEmpleado.objects.filter(objetivo=o)
        cargos = ObjetivoCargo.objects.filter(objetivo=o)
        progress_vals = []
        if emps.exists():
            for x in emps:
                progress_vals.append(100 if x.completado else 0)
        if cargos.exists():
            for x in cargos:
                progress_vals.append(100 if x.completado else 0)
        if progress_vals:
            avg_progress = sum(progress_vals) // len(progress_vals)
        else:
            avg_progress = 0
        items.append({
            "title": o.titulo or (o.descripcion or "Objetivo"),
            "type": "Recurrente" if o.es_recurrente else "Único",
            "owner": o.departamento.nombre if getattr(o, 'departamento', None) else (o.creado_por.get_full_name() if getattr(o, 'creado_por', None) else None),
            "progress": int(avg_progress)
        })
    return JsonResponse({"items": items})
