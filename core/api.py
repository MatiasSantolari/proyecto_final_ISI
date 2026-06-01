from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q, Min
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from datetime import timedelta, date
from django.db.models.functions import ExtractMonth, ExtractYear
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from django.utils import translation
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
import calendar
from django.db.models.functions import Round
import locale
from django.db.models import Sum, Q
from decimal import Decimal


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
    HistorialContrato,
)


def to_float(value):
    try:
        return float(value) if value is not None else 0.0
    except:
        return 0.0

####
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, '')



@require_GET
@login_required
def api_kpis(request):
    today = timezone.localdate()
    rol_actual = request.session.get('rol_actual', request.user.rol)

    empleados_qs = Empleado.objects.filter(estado='activo')
    asistencias_qs = HistorialAsistencia.objects.all()
    nominas_qs = Nomina.objects.all()
    evaluaciones_qs = EvaluacionEmpleado.objects.all()

    if rol_actual in ['jefe', 'gerente']:
        try:
            empleado_usuario = request.user.persona.empleado

            departamento = empleado_usuario.departamento_actual()

            if departamento:
                empleados_qs = empleados_qs.filter(
                    empleadocargo__cargo__cargodepartamento__departamento=departamento
                ).distinct()

                asistencias_qs = asistencias_qs.filter(
                    empleado__empleadocargo__cargo__cargodepartamento__departamento=departamento
                ).distinct()

                nominas_qs = nominas_qs.filter(
                    empleado__empleadocargo__cargo__cargodepartamento__departamento=departamento
                ).distinct()

                evaluaciones_qs = evaluaciones_qs.filter(
                    empleado__empleadocargo__cargo__cargodepartamento__departamento=departamento
                ).distinct()
            else:
                empleados_qs = empleados_qs.none()
                asistencias_qs = asistencias_qs.none()
                nominas_qs = nominas_qs.none()
                evaluaciones_qs = evaluaciones_qs.none()

        except (AttributeError, Empleado.DoesNotExist):
            return JsonResponse({"error": "Usuario sin perfil de empleado"}, status=403)


    nombre_mes_actual = today.strftime('%B %Y').capitalize()
    absences_count = asistencias_qs.filter(
        fecha_asistencia__month=today.month,
        fecha_asistencia__year=today.year,
        confirmado=False,
        licencia=False
    ).distinct().count()

    nominas_validas = nominas_qs.exclude(estado__iexact="anulado")
    ultima_nomina = nominas_validas.order_by('-fecha_generacion').first()

    if ultima_nomina:
        fecha_datos = ultima_nomina.fecha_generacion
        nombre_mes_costo = fecha_datos.strftime('%B %Y').capitalize()

        payroll_cost = nominas_validas.filter(
            fecha_generacion__month=fecha_datos.month,
            fecha_generacion__year=fecha_datos.year
        ).aggregate(total=Sum('monto_bruto'))['total'] or 0
    else:
        nombre_mes_costo = "Sin datos"
        payroll_cost = 0

    start_eval = today - timedelta(days=365)
    rango_eval = f"{start_eval.strftime('%b %Y')} - {today.strftime('%b %Y')}".capitalize()

    eval_avg = evaluaciones_qs.filter(
        fecha_registro__gte=start_eval,
        empleado__estado='activo'
    ).aggregate(avg=Avg('calificacion_final'))['avg'] or 0

    return JsonResponse({
        "employees_total": empleados_qs.distinct().count(),
        "absences_count": absences_count,
        "absences_month_name": nombre_mes_actual,
        "payroll_cost": float(payroll_cost),
        "payroll_month_name": nombre_mes_costo,
        "eval_avg": round(float(eval_avg), 2),
        "eval_range": rango_eval
    })



@require_GET
@login_required
def api_vacaciones(request):
    hoy = timezone.localdate()
    periodo_solicitado = request.GET.get('periodo')
    if not periodo_solicitado or periodo_solicitado.strip() == "":
        periodo_solicitado = '1m'

    rol_actual = request.session.get('rol_actual', request.user.rol)

    periodos_map = {
        '1m': 0, '2m': 2, '3m': 3, '6m': 6, '12m': 12,
        '24m': 24, '60m': 60
    }

    base_qs = VacacionesSolicitud.objects.all()

    if rol_actual in ['jefe', 'gerente']:
        try:
            depto = request.user.persona.empleado.departamento_actual()
            if depto:
                base_qs = base_qs.filter(
                    empleado__empleadocargo__cargo__cargodepartamento__departamento=depto,
                    empleado__empleadocargo__fecha_fin__isnull=True
                ).distinct()
            else:
                base_qs = base_qs.none()
        except (AttributeError, Empleado.DoesNotExist):
            base_qs = base_qs.none()

    if periodo_solicitado == 'all':
        primera_sol = base_qs.order_by('fecha_solicitud').only('fecha_solicitud').first()
        start_date = primera_sol.fecha_solicitud if primera_sol else hoy.replace(day=1)
        end_date = hoy
    else:
        meses = periodos_map.get(periodo_solicitado, 0)
        start_date = (hoy - relativedelta(months=meses)).replace(day=1) if meses > 0 else hoy.replace(day=1)
        end_date = hoy

    metrics = base_qs.filter(fecha_solicitud__range=[start_date, end_date]).aggregate(
        total=Count('id'),
        approved=Count('id', filter=Q(estado='aprobado')),
        pending=Count('id', filter=Q(estado='pendiente')),
        rejected=Count('id', filter=Q(estado='rechazado')),
        cancelled=Count('id', filter=Q(estado='cancelado'))
    )

    return JsonResponse({
        "total": metrics['total'] or 0,
        "approved": metrics['approved'] or 0,
        "pending": metrics['pending'] or 0,
        "rejected": metrics['rejected'] or 0,
        "cancelled": metrics['cancelled'] or 0,
        "start_date_formatted": start_date.strftime('%d %b %Y'),
        "end_date_formatted": end_date.strftime('%d %b %Y'),
        "active_period": periodo_solicitado
    })



@require_GET
@login_required
def api_asistencias(request):
    today = timezone.localdate()
    periodo_solicitado = request.GET.get('periodo', '30d')
    rol_actual = request.session.get('rol_actual', request.user.rol)

    base_qs = HistorialAsistencia.objects.all()
    if rol_actual in ['jefe', 'gerente']:
        try:
            depto = request.user.persona.empleado.departamento_actual()
            if depto:
                base_qs = base_qs.filter(
                    empleado__empleadocargo__cargo__cargodepartamento__departamento=depto,
                    empleado__empleadocargo__fecha_fin__isnull=True
                ).distinct()
            else:
                base_qs = base_qs.none()
        except (AttributeError, Empleado.DoesNotExist):
            base_qs = base_qs.none()

    periodos_config = {
        '30d': {'days': 30, 'group': 'day'},
        '2m':  {'days': 60, 'group': 'week'},
        '3m':  {'days': 90, 'group': 'week'},
        '6m':  {'days': 180, 'group': 'month'},
        '12m': {'days': 365, 'group': 'month'},
        '24m': {'days': 730, 'group': 'month'},
        '60m': {'days': 1825, 'group': 'month'},
    }

    if periodo_solicitado == 'all':
        primera_asistencia = base_qs.order_by('fecha_asistencia').only('fecha_asistencia').first()
        start_date = primera_asistencia.fecha_asistencia if primera_asistencia else today - timedelta(days=29)
        group_by = 'month'
    elif periodo_solicitado in periodos_config:
        conf = periodos_config[periodo_solicitado]
        start_date = today - timedelta(days=conf['days'] - 1)
        group_by = conf['group']
    else:
        start_date = today - timedelta(days=29)
        group_by = 'day'

    qs = base_qs.filter(fecha_asistencia__range=[start_date, today])

    if group_by == 'day':
        trunc_func = TruncDay('fecha_asistencia')
    elif group_by == 'week':
        trunc_func = TruncWeek('fecha_asistencia')
    else:
        trunc_func = TruncMonth('fecha_asistencia')

    metrics = qs.annotate(periodo_label=trunc_func).values('periodo_label').annotate(
        c_present=Count('id', filter=Q(confirmado=True, tardanza=False, licencia=False)),
        c_late=Count('id', filter=Q(tardanza=True, licencia=False)),
        c_ausent=Count('id', filter=Q(confirmado=False, licencia=False)),
        c_licenses=Count('id', filter=Q(licencia=True))
    ).order_by('periodo_label')

    metrics_dict = {m['periodo_label']: m for m in metrics}
    labels, present, ausent, late, licenses = [], [], [], [], []

    if group_by == 'day':
        days_back = (today - start_date).days + 1
        for i in range(days_back):
            d = start_date + timedelta(days=i)
            labels.append(d.strftime('%d %b'))
            m = metrics_dict.get(d, {'c_present': 0, 'c_late': 0, 'c_ausent': 0, 'c_licenses': 0})
            present.append(m['c_present'])
            late.append(m['c_late'])
            ausent.append(m['c_ausent'])
            licenses.append(m['c_licenses'])

    elif group_by == 'month':
        current_date = start_date.replace(day=1)
        while current_date <= today:
            labels.append(current_date.strftime('%b %Y'))
            m = metrics_dict.get(current_date, {'c_present': 0, 'c_late': 0, 'c_ausent': 0, 'c_licenses': 0})
            present.append(m['c_present'])
            late.append(m['c_late'])
            ausent.append(m['c_ausent'])
            licenses.append(m['c_licenses'])
            current_date += relativedelta(months=1)

    elif group_by == 'week':
        current_date = start_date - timedelta(days=start_date.weekday())
        while current_date <= today:
            if current_date + timedelta(days=6) < start_date:
                current_date += timedelta(days=7)
                continue
            week_end = min(current_date + timedelta(days=6), today)
            labels.append(f"{current_date.strftime('%d %b')} - {week_end.strftime('%d %b')}")

            m = metrics_dict.get(current_date, {'c_present': 0, 'c_late': 0, 'c_ausent': 0, 'c_licenses': 0})
            present.append(m['c_present'])
            late.append(m['c_late'])
            ausent.append(m['c_ausent'])
            licenses.append(m['c_licenses'])
            current_date += timedelta(days=7)

    return JsonResponse({
        "labels": labels,
        "present": present,
        "late": late,
        "ausent": ausent,
        "licenses": licenses,
        "start_date_formatted": start_date.strftime('%d %b %Y'),
        "end_date_formatted": today.strftime('%d %b %Y'),
        "active_period": periodo_solicitado
    })




def to_float(value):
    try:
        return float(value) if value is not None else 0.0
    except:
        return 0.0


@require_GET
@login_required
def api_evaluaciones(request):
    today = timezone.localdate()

    periodo_solicitado = request.GET.get('periodo')
    if not periodo_solicitado or periodo_solicitado.strip() == "":
        periodo_solicitado = '12m'

    rol_actual = request.session.get('rol_actual', request.user.rol)

    periodos_map = {
        '1m': 1, '2m': 2, '3m': 3, '6m': 6, '12m': 12,
        '24m': 24, '60m': 60
    }

    evals_qs = EvaluacionEmpleado.objects.exclude(calificacion_final__isnull=True)

    if periodo_solicitado == 'all':
        primera_eval = evals_qs.order_by('fecha_registro').only('fecha_registro').first()
        start_date = primera_eval.fecha_registro if primera_eval else today - relativedelta(months=11)
    else:
        meses_atras = periodos_map.get(periodo_solicitado, 12)
        start_date = today - relativedelta(months=meses_atras)
        evals_qs = evals_qs.filter(fecha_registro__gte=start_date)

    if rol_actual in ['jefe', 'gerente']:
        try:
            depto = request.user.persona.empleado.departamento_actual()
            if depto:
                evals_qs = evals_qs.filter(
                    empleado__empleadocargo__cargo__cargodepartamento__departamento=depto,
                    empleado__empleadocargo__fecha_fin__isnull=True
                ).distinct()
            else:
                evals_qs = evals_qs.none()
        except (AttributeError, Empleado.DoesNotExist):
            evals_qs = evals_qs.none()

    metrics = evals_qs.annotate(
        nota_redondeada=Round('calificacion_final')
    ).values('nota_redondeada').annotate(
        total=Count('id')
    )

    counts = [0] * 10
    for m in metrics:
        try:
            nota = int(m['nota_redondeada'])
            if 1 <= nota <= 10:
                counts[nota - 1] = m['total']
        except (ValueError, TypeError):
            continue

    return JsonResponse({
        "labels": ["1","2","3","4","5","6","7","8","9","10"],
        "counts": counts,
        "start_date_formatted": start_date.strftime('%b %Y') if start_date else "Inicio",
        "end_date_formatted": today.strftime('%b %Y'),
    })





def to_float(val):
    if val is None:
        return 0.0
    return float(val)


@require_GET
@login_required
def api_nominas(request):
    rol_actual = request.session.get('rol_actual', request.user.rol)
    periodo_solicitado = request.GET.get('periodo', '1m')

    qs_base = Nomina.objects.all()

    if rol_actual in ['jefe', 'gerente']:
        try:
            depto = request.user.persona.empleado.departamento_actual()
            if depto:
                empleados_ids = Empleado.objects.filter(
                    empleadocargo__cargo__cargodepartamento__departamento=depto
                ).values_list('id', flat=True).distinct()
                qs_base = qs_base.filter(empleado_id__in=empleados_ids)
            else:
                qs_base = qs_base.none()
        except (AttributeError, Empleado.DoesNotExist):
            qs_base = qs_base.none()

    ultima_nomina = qs_base.order_by('-fecha_generacion').only('fecha_generacion').first()

    if not ultima_nomina:
        return JsonResponse({
            "base": 0.0, "benefits": 0.0, "discounts": 0.0, "extras": 0.0,
            "start_date_formatted": "Sin datos", "end_date_formatted": ""
        })

    ultimo_mes_con_datos = ultima_nomina.fecha_generacion.replace(day=1)
    periodos_map = {'1m': 1, '2m': 2, '3m': 3, '6m': 6, '12m': 12, '24m': 24, '60m': 60}
    end_date = ultimo_mes_con_datos + relativedelta(months=1, days=-1)

    if periodo_solicitado == 'all':
        primera_nom = qs_base.order_by('fecha_generacion').only('fecha_generacion').first()
        start_date = primera_nom.fecha_generacion.replace(day=1) if primera_nom else ultimo_mes_con_datos
    else:
        num_months = periodos_map.get(periodo_solicitado, 1)
        start_date = ultimo_mes_con_datos - relativedelta(months=(num_months - 1))

    nominas_periodo = qs_base.filter(fecha_generacion__range=[start_date, end_date]).exclude(estado__iexact="anulado")

    empleados_con_nomina_ids = nominas_periodo.values_list('empleado_id', flat=True).distinct()

    contratos_vigentes = HistorialContrato.objects.filter(
        empleado_id__in=empleados_con_nomina_ids,
        fecha_inicio__lte=end_date
    ).filter(
        Q(fecha_fin__gte=start_date) | Q(fecha_fin__isnull=True)
    )

    total_extras = Decimal('0.00')
    for contrato in contratos_vigentes:
        total_nominas_empleado = nominas_periodo.filter(empleado=contrato.empleado).count()
        if contrato.monto_extra_pactado:
            total_extras += contrato.monto_extra_pactado * Decimal(str(total_nominas_empleado))

    totales = nominas_periodo.aggregate(
        s_bruto=Sum('monto_bruto'),
        s_beneficios=Sum('total_beneficios'),
        s_descuentos=Sum('total_descuentos')
    )

    bruto_total = totales['s_bruto'] or Decimal('0.00')
    benefits = totales['s_beneficios'] or Decimal('0.00')
    discounts = totales['s_descuentos'] or Decimal('0.00')

    base_pura = bruto_total - benefits - total_extras

    if base_pura < 0:
        base_pura = Decimal('0.00')

    return JsonResponse({
        "base": to_float(base_pura),
        "benefits": to_float(benefits),
        "discounts": to_float(discounts),
        "extras": to_float(total_extras),  
        "start_date_formatted": start_date.strftime('%b. %Y').capitalize(),
        "end_date_formatted": end_date.strftime('%b. %Y').capitalize() if periodo_solicitado != '1m' else start_date.strftime('%b. %Y').capitalize(),
    })



def calcular_costos_mensuales_por_anio(year, depto_filter):
    costs = Nomina.objects.filter(
        fecha_generacion__year=year,
        **depto_filter
    ).exclude(
        estado__iexact="anulado"
    ).annotate(
        month=ExtractMonth('fecha_generacion')
    ).values('month').annotate(
        total_cost=Sum('monto_bruto')  
    ).order_by('month')

    monthly_data = {item['month']: float(item['total_cost'] or 0) for item in costs}
    return [monthly_data.get(month, 0) for month in range(1, 13)]



@require_GET
@login_required
def api_labor_cost_comparison(request):
    today = timezone.localdate()
    rol_actual = request.session.get('rol_actual', request.user.rol)
    year1 = int(request.GET.get('year1', today.year - 1))
    year2 = int(request.GET.get('year2', today.year))

    depto_filter = {}
    if rol_actual in ['jefe', 'gerente']:
        try:
            empleado_usuario = request.user.persona.empleado
            departamento = empleado_usuario.departamento_actual()
            if departamento:
                depto_filter = {
                    'empleado__empleadocargo__cargo__cargodepartamento__departamento': departamento,
                    'empleado__empleadocargo__fecha_fin__isnull': True
                }
            else:
                depto_filter = {'id__isnull': True}
        except (AttributeError, Empleado.DoesNotExist):
            depto_filter = {'id__isnull': True}

    data_year1 = calcular_costos_mensuales_por_anio(year1, depto_filter)
    data_year2 = calcular_costos_mensuales_por_anio(year2, depto_filter)

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
    rol_actual = request.session.get('rol_actual', request.user.rol)

    if rol_actual in ['jefe', 'gerente']:
        try:
            empleado_usuario = request.user.persona.empleado
            depto_usuario = empleado_usuario.departamento_actual()
            if depto_usuario:
                depts = Departamento.objects.filter(id=depto_usuario.id)
            else:
                depts = Departamento.objects.none()
        except (AttributeError, Empleado.DoesNotExist):
            depts = Departamento.objects.none()
    else:
        depts = Departamento.objects.all()

    labels = []
    counts = []

    for d in depts:
        cargos_ids = CargoDepartamento.objects.filter(departamento=d).values_list('cargo_id', flat=True)
        emp_count = EmpleadoCargo.objects.filter(
            cargo_id__in=cargos_ids,
            fecha_fin__isnull=True
        ).values('empleado').distinct().count()

        labels.append(d.nombre)
        counts.append(emp_count)

    return JsonResponse({"labels": labels, "counts": counts})




@require_GET
@login_required
def api_objetivos(request):
    rol_actual = request.session.get('rol_actual', request.user.rol)
    department_id = request.GET.get('departamento_id')

    objs_queryset = Objetivo.objects.filter(activo=True).select_related(
        'departamento', 'creado_por__persona'
    ).annotate(
        total_asig=Count('objetivoempleado'),
        total_comp=Count('objetivoempleado', filter=Q(objetivoempleado__completado=True)),
        tiene_cargo=Count('objetivoempleado', filter=Q(objetivoempleado__cargo__isnull=False))
    ).order_by('-fecha_creacion')

    if rol_actual in ['jefe', 'gerente']:
        try:
            empleado_usuario = request.user.persona.empleado
            depto_usuario = empleado_usuario.departamento_actual()

            if depto_usuario:
                objs_queryset = objs_queryset.filter(departamento=depto_usuario)
            else:
                return JsonResponse({"items": []})
        except (AttributeError, Empleado.DoesNotExist):
            return JsonResponse({"items": []})

    elif department_id and department_id != 'todos':
        try:
            objs_queryset = objs_queryset.filter(departamento_id=int(department_id))
        except ValueError:
            pass

    items = []
    for o in objs_queryset[:50]:
        total = o.total_asig

        if total > 0:
            avg_progress = (o.total_comp * 100) // total
            tipo_label = "Por Cargo" if o.tiene_cargo > 0 else "Directo"
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
    rol_actual = request.session.get('rol_actual', request.user.rol)

    periodo_solicitado = request.GET.get('periodo')
    if not periodo_solicitado or periodo_solicitado.strip() == "":
        periodo_solicitado = '6m'

    periodos_map = {
        '1m': 1, '2m': 2, '3m': 3, '6m': 6, '12m': 12,
        '24m': 24, '60m': 60
    }

    base_qs = CapacitacionEmpleado.objects.all()

    if rol_actual in ['jefe', 'gerente']:
        try:
            depto = request.user.persona.empleado.departamento_actual()
            if depto:
                base_qs = base_qs.filter(
                    empleado__empleadocargo__cargo__cargodepartamento__departamento=depto,
                    empleado__empleadocargo__fecha_fin__isnull=True
                ).distinct()
            else:
                return JsonResponse({"labels": [], "internas": [], "externas": []})
        except (AttributeError, Empleado.DoesNotExist):
            return JsonResponse({"labels": [], "internas": [], "externas": []})

    if periodo_solicitado == 'all':
        primera_insc = base_qs.order_by('fecha_inscripcion').only('fecha_inscripcion').first()
        start_date = primera_insc.fecha_inscripcion.replace(day=1) if primera_insc else today.replace(day=1)
    else:
        num_months = periodos_map.get(periodo_solicitado, 6)
        start_date = (today.replace(day=1) - relativedelta(months=num_months - 1))

    qs_final = base_qs.filter(fecha_inscripcion__range=[start_date, today])

    metrics = qs_final.annotate(
        mes_label=TruncMonth('fecha_inscripcion')
    ).values('mes_label').annotate(
        c_internas=Count('id', filter=Q(capacitacion__es_externo=False)),
        c_externas=Count('id', filter=Q(capacitacion__es_externo=True))
    ).order_by('mes_label')

    metrics_dict = {m['mes_label']: m for m in metrics}

    labels, internas, externas = [], [], []
    current_date = start_date

    while current_date <= today:
        labels.append(current_date.strftime('%b %y').capitalize())
        m = metrics_dict.get(current_date, {'c_internas': 0, 'c_externas': 0})

        internas.append(m['c_internas'])
        externas.append(m['c_externas'])
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

    from django.utils.formats import date_format
    fecha_str = date_format(hoy, "l, d \d\e F Y").capitalize()

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

    try:
        empleado = Empleado.objects.get(id=persona.id)
    except Empleado.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado'}, status=44)

    hoy = timezone.localtime(timezone.now()).date()
    primer_dia_mes = hoy.replace(day=1)

    total_dias_laborables_contados = 0
    dias_asistidos = 0

    current_day = primer_dia_mes
    while current_day <= hoy:
        if current_day.weekday() not in [5, 6]:

            registro_asistencia_dia = HistorialAsistencia.objects.filter(
                empleado=empleado,
                fecha_asistencia=current_day
            ).first()

            if registro_asistencia_dia and registro_asistencia_dia.licencia:
                pass
            else:
                total_dias_laborables_contados += 1
                if registro_asistencia_dia and registro_asistencia_dia.confirmado:
                    dias_asistidos += 1

        current_day += timedelta(days=1)

    porcentaje_asistencia = (dias_asistidos / total_dias_laborables_contados * 100) if total_dias_laborables_contados > 0 else 0

    registro_hoy = HistorialAsistencia.objects.filter(empleado=empleado, fecha_asistencia=hoy).first()

    estado_hoy = "Nada marcado"
    if registro_hoy:
        if registro_hoy.licencia:
            estado_hoy = "De Licencia"
        elif registro_hoy.hora_entrada and not registro_hoy.hora_salida:
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
