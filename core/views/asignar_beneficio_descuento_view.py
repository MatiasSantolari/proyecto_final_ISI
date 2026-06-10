from django.http import HttpResponse, JsonResponse
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
from django.db.models import Q
from django.core.paginator import Paginator


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
    search_texto = request.GET.get('search_texto', '').strip()
    hoy = now().date()

    empleados_qs = Empleado.objects.all()
    user_empleado = _get_empleado_de_user(request.user)
    rol_actual = request.session.get("rol_actual", None)

    if rol_actual == "admin":
        if departamento_sel:
            empleados_qs = empleados_qs.filter(
                empleadocargo__cargo__cargodepartamento__departamento__nombre=departamento_sel,
                empleadocargo__fecha_fin__isnull=True
            )
        mostrar_filtro_departamentos = True

    elif rol_actual == "jefe" and user_empleado:
        cargo_act = user_empleado.empleadocargo_set.filter(
            fecha_inicio__lte=hoy, fecha_fin__isnull=True
        ).order_by('-fecha_inicio').first()

        if cargo_act and cargo_act.cargo.es_jefe:
            dept_ids = list(cargo_act.cargo.cargodepartamento_set.values_list('departamento_id', flat=True))
            empleados_qs = empleados_qs.filter(
                empleadocargo__cargo__cargodepartamento__departamento_id__in=dept_ids,
                empleadocargo__fecha_fin__isnull=True
            )
            departamento_sel = cargo_act.cargo.cargodepartamento_set.first().departamento.nombre if cargo_act.cargo.cargodepartamento_set.exists() else ''
        mostrar_filtro_departamentos = False

    else:
        if user_empleado:
            empleados_qs = Empleado.objects.filter(id=user_empleado.id)
        else:
            empleados_qs = Empleado.objects.none()
        mostrar_filtro_departamentos = False

    if search_texto:
        empleados_qs = empleados_qs.filter(
            Q(nombre__icontains=search_texto) |
            Q(apellido__icontains=search_texto) |
            Q(dni__icontains=search_texto)
        )

    empleados_qs = empleados_qs.distinct().order_by('apellido', 'nombre')

    paginator = Paginator(empleados_qs, 10) 
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    descuentos_disponibles = Descuento.objects.filter(fijo=False, activo=True).order_by('descripcion')
    beneficios_disponibles = Beneficio.objects.filter(
            fijo=False, 
            activo=True,
        ).exclude(
            Q(descripcion__icontains='antigüedad') | 
            Q(descripcion__icontains='antiguedad') | 
            Q(descripcion__icontains='asistencia')
        ).order_by('descripcion')
 
    departamentos = Departamento.objects.filter(activo=True).order_by('nombre')

    context = {
        'empleados': page_obj, 
        'page_obj': page_obj, 
        'departamentos': departamentos,
        'departamento_sel': departamento_sel,
        'descuentos_disponibles': descuentos_disponibles,
        'beneficios_disponibles': beneficios_disponibles,
        'mostrar_filtro_departamentos': mostrar_filtro_departamentos,
        'texto_buscado': search_texto,
    }
    return render(request, 'asignador_beneficios_descuentos.html', context)



@login_required
def asignar_a_empleados(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Método inválido")

    tipo = request.POST.get('tipo')  
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
@require_POST
def eliminar_asignacion_descuento(request, id_asignacion):
    """Elimina la relación mensual de un descuento asignado a un empleado"""
    asignacion = get_object_or_404(DescuentoEmpleadoNomina, id=id_asignacion)
    
    if asignacion.nomina is not None:
        return JsonResponse({"status": "error", "message": "No es posible eliminar una relación que ya fue liquidada en una nómina cerrada."}, status=400)

    user_empleado = _get_empleado_de_user(request.user)
    hoy = now().date()
    
    if _user_es_admin(request.user, empleado_obj=user_empleado):
        empleados_permitidos_qs = Empleado.objects.all()
    else:
        if user_empleado:
            cargo_act = user_empleado.empleadocargo_set.filter(fecha_inicio__lte=hoy, fecha_fin__isnull=True).order_by('-fecha_inicio').first()
            if cargo_act and cargo_act.cargo.es_jefe:
                dept_ids = list(cargo_act.cargo.cargodepartamento_set.values_list('departamento_id', flat=True))
                empleados_permitidos_qs = Empleado.objects.filter(empleadocargo__cargo__cargodepartamento__departamento_id__in=dept_ids, empleadocargo__fecha_fin__isnull=True).distinct()
            else:
                empleados_permitidos_qs = Empleado.objects.filter(id=user_empleado.id)
        else:
            empleados_permitidos_qs = Empleado.objects.none()

    if asignacion.empleado_id not in set(empleados_permitidos_qs.values_list('id', flat=True)):
        return JsonResponse({"status": "error", "message": "Acceso denegado: No posee permisos para modificar las novedades de este colaborador."}, status=403)

    asignacion.delete()
    return JsonResponse({"status": "success", "message": "Relación de descuento eliminada con éxito."})



@login_required
@require_POST
def eliminar_asignacion_beneficio(request, id_asignacion):
    """Elimina la relación mensual de un beneficio asignado a un empleado"""
    asignacion = get_object_or_404(BeneficioEmpleadoNomina, id=id_asignacion)
    
    if asignacion.nomina is not None:
        return JsonResponse({"status": "error", "message": "No es posible eliminar una relación que ya fue liquidada en una nómina cerrada."}, status=400)

    user_empleado = _get_empleado_de_user(request.user)
    hoy = now().date()
    
    if _user_es_admin(request.user, empleado_obj=user_empleado):
        empleados_permitidos_qs = Empleado.objects.all()
    else:
        if user_empleado:
            cargo_act = user_empleado.empleadocargo_set.filter(fecha_inicio__lte=hoy, fecha_fin__isnull=True).order_by('-fecha_inicio').first()
            if cargo_act and cargo_act.cargo.es_jefe:
                dept_ids = list(cargo_act.cargo.cargodepartamento_set.values_list('departamento_id', flat=True))
                empleados_permitidos_qs = Empleado.objects.filter(empleadocargo__cargo__cargodepartamento__departamento_id__in=dept_ids, empleadocargo__fecha_fin__isnull=True).distinct()
            else:
                empleados_permitidos_qs = Empleado.objects.filter(id=user_empleado.id)
        else:
            empleados_permitidos_qs = Empleado.objects.none()

    if asignacion.empleado_id not in set(empleados_permitidos_qs.values_list('id', flat=True)):
        return JsonResponse({"status": "error", "message": "Acceso denegado: No posee permisos para modificar las novedades de este colaborador."}, status=403)

    asignacion.delete()
    return JsonResponse({"status": "success", "message": "Relación de beneficio eliminada con éxito."})



@login_required
def ver_asignaciones_empleado(request, empleado_id):
    """
    Endpoint AJAX que recopila en una única respuesta JSON tanto los conceptos
    fijos generales por ley como las asignaciones variables del mes del empleado.
    """
    empleado = get_object_or_404(Empleado, pk=empleado_id)

    descuentos_list = []

    descuentos_fijos = Descuento.objects.filter(fijo=True, activo=True).order_by('descripcion')
    for df in descuentos_fijos:
        descuentos_list.append({
            "id": None, 
            "descripcion": f"{df.descripcion} (Fijo de Sistema)",
            "monto": float(df.monto) if df.monto is not None else None,
            "porcentaje": float(df.porcentaje) if df.porcentaje is not None else None,
        })

    descuentos_variables = DescuentoEmpleadoNomina.objects.filter(
        empleado=empleado, 
        nomina__isnull=True,
        descuento__activo=True 
    ).select_related('descuento').order_by('id')
    
    for dv in descuentos_variables:
        desc_obj = dv.descuento
        descuentos_list.append({
            "id": dv.id,
            "descripcion": getattr(desc_obj, 'descripcion', '') or getattr(desc_obj, 'nombre', '') or '',
            "monto": float(desc_obj.monto) if desc_obj.monto is not None else None,
            "porcentaje": float(desc_obj.porcentaje) if desc_obj.porcentaje is not None else None,
        })

    beneficios_list = []

    beneficios_fijos = Beneficio.objects.filter(fijo=True, activo=True).order_by('descripcion')
    for bf in beneficios_fijos:
        beneficios_list.append({
            "id": None,
            "descripcion": f"{bf.descripcion} (Fijo de Sistema)",
            "monto": float(bf.monto) if bf.monto is not None else None,
            "porcentaje": float(bf.porcentaje) if bf.porcentaje is not None else None,
        })

    beneficios_variables = BeneficioEmpleadoNomina.objects.filter(
        empleado=empleado, 
        nomina__isnull=True,
        beneficio__activo=True 
    ).select_related('beneficio').order_by('id')
    
    for bv in beneficios_variables:
        ben_obj = bv.beneficio
        beneficios_list.append({
            "id": bv.id,
            "descripcion": getattr(ben_obj, 'descripcion', '') or getattr(ben_obj, 'nombre', '') or '',
            "monto": float(ben_obj.monto) if ben_obj.monto is not None else None,
            "porcentaje": float(ben_obj.porcentaje) if ben_obj.porcentaje is not None else None,
        })

    return JsonResponse({
        "empleado": f"{empleado.nombre} {empleado.apellido}",
        "descuentos": descuentos_list,
        "beneficios": beneficios_list,
    })
