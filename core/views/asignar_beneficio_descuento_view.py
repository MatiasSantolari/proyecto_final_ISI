from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseBadRequest



def _get_empleado_de_user(user):
    emp = getattr(user, 'empleado', None)
    if emp:
        return emp

    try:
        emp = Empleado.objects.filter(persona__usuario=user).first()
        if emp:
            return emp
    except Exception:
        pass

    try:
        emp = Empleado.objects.filter(persona__user=user).first()
        if emp:
            return emp
    except Exception:
        pass

    try:
        emp = Empleado.objects.filter(persona__email=getattr(user, 'email', None)).first()
        if emp:
            return emp
    except Exception:
        pass

    return None




def _user_es_admin(user, empleado_obj=None):
    rol = getattr(user, 'rol', None)
    if rol == 'admin':
        return True

    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return True

    empleado_obj = empleado_obj or _get_empleado_de_user(user)
    if not empleado_obj:
        return False

    hoy = now().date()
    cargo_act = empleado_obj.empleadocargo_set.filter(
        fecha_inicio__lte=hoy, fecha_fin__isnull=True
    ).order_by('-fecha_inicio').first()

    if cargo_act and cargo_act.cargo.es_jefe and cargo_act.cargo.es_gerente:
        return True

    return False




@login_required
def asignador_view(request):
    departamento_sel = request.GET.get('departamento', '')
    hoy = now().date()

    empleados_qs = Empleado.objects.all()
    user_empleado = _get_empleado_de_user(request.user)
    rol_actual = request.session.get("rol_actual", None)

    # --- Si es admin ---
    if rol_actual == "admin":
        if departamento_sel:
            empleados_qs = empleados_qs.filter(
                empleadocargo__cargo__cargodepartamento__departamento__nombre=departamento_sel,
                empleadocargo__fecha_fin__isnull=True
            ).distinct()
        mostrar_filtro_departamentos = True

    # --- Si es jefe ---
    elif rol_actual == "jefe" and user_empleado:
        cargo_act = user_empleado.empleadocargo_set.filter(
            fecha_inicio__lte=hoy, fecha_fin__isnull=True
        ).order_by('-fecha_inicio').first()

        if cargo_act and cargo_act.cargo.es_jefe:
            dept_ids = list(cargo_act.cargo.cargodepartamento_set.values_list('departamento_id', flat=True))
            empleados_qs = empleados_qs.filter(
                empleadocargo__cargo__cargodepartamento__departamento_id__in=dept_ids,
                empleadocargo__fecha_fin__isnull=True
            ).distinct()
            # forzar el filtro por el depto del jefe
            departamento_sel = cargo_act.cargo.cargodepartamento_set.first().departamento.nombre if cargo_act.cargo.cargodepartamento_set.exists() else ''
        mostrar_filtro_departamentos = False

    # --- Si es empleado normal ---
    else:
        if user_empleado:
            empleados_qs = Empleado.objects.filter(id=user_empleado.id)
        else:
            empleados_qs = Empleado.objects.none()
        mostrar_filtro_departamentos = False

    empleados_qs = empleados_qs.order_by('apellido', 'nombre')

    descuentos_disponibles = Descuento.objects.filter(fijo=False, activo=True).order_by('descripcion')
    beneficios_disponibles = Beneficio.objects.filter(fijo=False, activo=True).order_by('descripcion')
    departamentos = Departamento.objects.all().order_by('nombre')

    context = {
        'empleados': empleados_qs,
        'departamentos': departamentos,
        'departamento_sel': departamento_sel,
        'descuentos_disponibles': descuentos_disponibles,
        'beneficios_disponibles': beneficios_disponibles,
        'mostrar_filtro_departamentos': mostrar_filtro_departamentos,
    }
    return render(request, 'asignador_beneficios_descuentos.html', context)




@login_required
def asignar_a_empleados(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Método inválido")

    tipo = request.POST.get('tipo')  # 'descuento' o 'beneficio'
    item_id = request.POST.get('item_id')
    empleado_ids = request.POST.getlist('empleado_ids[]') or request.POST.getlist('empleado_ids') or []

    if not tipo or not item_id or not empleado_ids:
        messages.error(request, "Debe seleccionar un descuento/beneficio y al menos un empleado.")
        return redirect('asignador_beneficios_descuentos')

    user_empleado = _get_empleado_de_user(request.user)
    hoy = now().date()
    if _user_es_admin(request.user, empleado_obj=user_empleado):
        empleados_permitidos_qs = Empleado.objects.all()
    else:
        if user_empleado:
            cargo_act = user_empleado.empleadocargo_set.filter(
                fecha_inicio__lte=hoy, fecha_fin__isnull=True
            ).order_by('-fecha_inicio').first()
            if cargo_act and cargo_act.cargo.es_jefe:
                dept_ids = list(cargo_act.cargo.cargodepartamento_set.values_list('departamento_id', flat=True))
                empleados_permitidos_qs = Empleado.objects.filter(
                    empleadocargo__cargo__cargodepartamento__departamento_id__in=dept_ids,
                    empleadocargo__fecha_fin__isnull=True
                ).distinct()
            else:
                empleados_permitidos_qs = Empleado.objects.filter(id=user_empleado.id)
        else:
            empleados_permitidos_qs = Empleado.objects.none()

    empleados_permitidos_ids = set(empleados_permitidos_qs.values_list('id', flat=True))

    creados = 0
    if tipo == "descuento":
        descuento = get_object_or_404(Descuento, pk=item_id, fijo=False, activo=True)
        for eid in empleado_ids:
            try:
                eid_int = int(eid)
            except ValueError:
                continue
            if eid_int not in empleados_permitidos_ids:
                continue
            exists = DescuentoEmpleadoNomina.objects.filter(empleado_id=eid_int, descuento=descuento, nomina__isnull=True).exists()
            if not exists:
                DescuentoEmpleadoNomina.objects.create(empleado_id=eid_int, descuento=descuento, nomina=None)
                creados += 1
        messages.success(request, f"Se asignaron {creados} registro(s) de descuento.")
    elif tipo == "beneficio":
        beneficio = get_object_or_404(Beneficio, pk=item_id, fijo=False, activo=True)
        for eid in empleado_ids:
            try:
                eid_int = int(eid)
            except ValueError:
                continue
            if eid_int not in empleados_permitidos_ids:
                continue
            exists = BeneficioEmpleadoNomina.objects.filter(empleado_id=eid_int, beneficio=beneficio, nomina__isnull=True).exists()
            if not exists:
                BeneficioEmpleadoNomina.objects.create(empleado_id=eid_int, beneficio=beneficio, nomina=None)
                creados += 1
        messages.success(request, f"Se asignaron {creados} registro(s) de beneficio.")
    else:
        messages.error(request, "Tipo inválido.")
        return redirect('asignador_beneficios_descuentos')

    return redirect('asignador_beneficios_descuentos')




@login_required
def ver_asignaciones_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, pk=empleado_id)

    descuentos = DescuentoEmpleadoNomina.objects.filter(empleado=empleado, nomina__isnull=True).select_related('descuento')
    beneficios = BeneficioEmpleadoNomina.objects.filter(empleado=empleado, nomina__isnull=True).select_related('beneficio')

    descuentos_list = [
        {
            "id": d.id,
            "descripcion": getattr(d.descuento, 'descripcion', '') or getattr(d.descuento, 'nombre', '') or '',
            "monto": float(d.descuento.monto) if d.descuento.monto is not None else None,
            "porcentaje": float(getattr(d.descuento, 'porcentaje', 0)) if getattr(d.descuento, 'porcentaje', None) is not None else None,
        }
        for d in descuentos
    ]
    beneficios_list = [
        {
            "id": b.id,
            "descripcion": getattr(b.beneficio, 'descripcion', '') or getattr(b.beneficio, 'nombre', '') or '',
            "monto": float(b.beneficio.monto) if b.beneficio.monto is not None else None,
            "porcentaje": float(getattr(b.beneficio, 'porcentaje', 0)) if getattr(b.beneficio, 'porcentaje', None) is not None else None,
        }
        for b in beneficios
    ]

    return JsonResponse({
        "empleado": f"{empleado.nombre} {empleado.apellido}",
        "descuentos": descuentos_list,
        "beneficios": beneficios_list,
    })
