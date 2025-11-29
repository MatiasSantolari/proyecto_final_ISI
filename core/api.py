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
    # últimos 30 días
    today = timezone.localdate()
    start = today - timedelta(days=29)
    labels = []
    present = []
    ausent = []
    late = []
    for i in range(30):
        d = start + timedelta(days=i)
        labels.append(d.isoformat())
        day_qs = HistorialAsistencia.objects.filter(fecha_asistencia=d)
        present.append(day_qs.filter(confirmado=True).count())
        late.append(day_qs.filter(tardanza=True).count())
        ausent.append(day_qs.filter(confirmado=False).count())
    return JsonResponse({"labels": labels, "present": present, "late": late, "ausent": ausent})


######RECORDAR HACER ANUAL
@require_GET
@login_required
def api_evaluaciones(request):
    today = timezone.localdate()
    start_date = today - timedelta(days=365) 
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
    return JsonResponse({"labels": ["1","2","3","4","5","6","7","8","9","10"], "counts": counts})


@require_GET
@login_required
def api_nominas(request):
    today = timezone.localdate()
    first = today.replace(day=1)
    qs = Nomina.objects.filter(fecha_generacion__gte=first)
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
        "state_counts": state_counts
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
