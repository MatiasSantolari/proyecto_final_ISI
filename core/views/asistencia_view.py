from django.http import HttpResponse, JsonResponse
from django.urls import reverse
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
from django.utils import timezone
import pytz
from django.core.paginator import Paginator


def _get_empleado_de_user(request):
    empleado_id = request.session.get("empleado_id")
    if empleado_id:
        try:
            return Empleado.objects.get(id=empleado_id)
        except Empleado.DoesNotExist:
            pass
    try:
        return Empleado.objects.get(usuario=request.user)
    except Empleado.DoesNotExist:
        return None



def _user_es_admin(user, empleado=None):
    empleado = empleado or _get_empleado_de_user(user)
    
    rol = getattr(user, 'rol', None)
    if rol == 'admin':
        return True
    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return True
    if not empleado:
        return False
    
    hoy = timezone.localtime(timezone.now()).date() 
    cargo_act = empleado.empleadocargo_set.filter(
        fecha_inicio__lte=hoy, fecha_fin__isnull=True
    ).order_by('-fecha_inicio').first()

    if cargo_act and cargo_act.cargo.es_jefe and cargo_act.cargo.es_gerente:
        return True

    return False



@login_required
def registrar_asistencia(request):
    empleado = _get_empleado_de_user(request)
    if not empleado:
        messages.error(request, "No se encontró empleado vinculado a este usuario.")
        return redirect("home")

    hora_actual = timezone.now().astimezone(pytz.timezone('America/Argentina/Buenos_Aires')).time()
    hoy = timezone.localtime(timezone.now()).date()

    asistencia = HistorialAsistencia.objects.filter(empleado=empleado, fecha_asistencia=hoy).first()

    historial_asistencias = HistorialAsistencia.objects.filter(empleado=empleado).order_by('-fecha_asistencia')

    paginator = Paginator(historial_asistencias, 10)
    page_number = request.GET.get('page') 
    page_obj = paginator.get_page(page_number)

    next_url = request.META.get('HTTP_REFERER', reverse('home'))
    
    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "entrada":
            if asistencia and asistencia.hora_entrada:
                messages.warning(request, "Ya registraste tu entrada hoy.")
            else:
                if not asistencia:
                    asistencia = HistorialAsistencia(
                        empleado=empleado,
                        fecha_asistencia=hoy,
                        confirmado=False,
                        tardanza=False
                    )
                asistencia.hora_entrada = hora_actual
                asistencia.save()
                messages.success(request, "Entrada registrada correctamente.")
        elif accion == "salida":
            if not asistencia or not asistencia.hora_entrada:
                messages.error(request, "No puedes registrar salida sin entrada previa.")
            elif asistencia.hora_salida:
                messages.warning(request, "Ya registraste tu salida hoy.")
            else:
                asistencia.hora_salida = hora_actual
                asistencia.save()
                messages.success(request, "Salida registrada correctamente.")
        return redirect(next_url)
    
    return render(request, "registrar_asistencia.html", {
        "asistencia_hoy": asistencia,
        "hoy": hoy,
        "page_obj": page_obj,
    })



@login_required
def confirmar_asistencias(request):
    hoy = timezone.localtime(timezone.now()).date() 
    departamento_sel = request.GET.get("departamento", "")
    page_number = request.GET.get("page", 1)
    user_empleado = _get_empleado_de_user(request)

    if _user_es_admin(request.user, empleado=user_empleado):
        asistencias_qs = HistorialAsistencia.objects.filter(fecha_asistencia=hoy)
        mostrar_filtro = True
        if departamento_sel:
            asistencias_qs = asistencias_qs.filter(
                empleado__empleadocargo__cargo__cargodepartamento__departamento__nombre=departamento_sel,
                empleado__empleadocargo__fecha_fin__isnull=True
            ).distinct()
    else:
        mostrar_filtro = False
        if user_empleado:
            cargo_act = user_empleado.empleadocargo_set.filter(
                fecha_inicio__lte=hoy, fecha_fin__isnull=True
            ).order_by("-fecha_inicio").first()
            if cargo_act and cargo_act.cargo.es_jefe:
                dept_ids = list(cargo_act.cargo.cargodepartamento_set.values_list("departamento_id", flat=True))
                asistencias_qs = HistorialAsistencia.objects.filter(
                    fecha_asistencia=hoy,
                    empleado__empleadocargo__cargo__cargodepartamento__departamento_id__in=dept_ids,
                    empleado__empleadocargo__fecha_fin__isnull=True
                ).distinct()
            else:
                asistencias_qs = HistorialAsistencia.objects.filter(empleado=user_empleado, fecha_asistencia=hoy)
        else:
            asistencias_qs = HistorialAsistencia.objects.none()

    paginator = Paginator(asistencias_qs.order_by('empleado__apellido'), 10)
    asistencias_page = paginator.get_page(page_number)

    departamentos = Departamento.objects.all().order_by("nombre")

    context = {
        "asistencias": asistencias_page,
        "departamentos": departamentos,
        "departamento_sel": departamento_sel,
        "mostrar_filtro_departamentos": mostrar_filtro,
        "paginator": paginator,
        "hoy": hoy,
    }
    return render(request, "confirmar_asistencias.html", context)




@login_required
def confirmar_asistencias_accion(request):
    if request.method != "POST":
        return redirect("confirmar_asistencias")

    ids = request.POST.getlist("asistencia_ids")
    accion = request.POST.get("accion")
    actualizados = 0
    hoy = timezone.localtime(timezone.now()).date() 

    if accion == "registrar_ausentes":
        user_empleado = _get_empleado_de_user(request)
        if _user_es_admin(request.user, empleado=user_empleado):
            empleados = Empleado.objects.all()
        else:
            cargo_act = user_empleado.empleadocargo_set.filter(
                fecha_inicio__lte=hoy, fecha_fin__isnull=True
            ).order_by("-fecha_inicio").first()
            if cargo_act and cargo_act.cargo.es_jefe:
                dept_ids = list(cargo_act.cargo.cargodepartamento_set.values_list("departamento_id", flat=True))
                empleados = Empleado.objects.filter(
                    empleadocargo__cargo__cargodepartamento__departamento_id__in=dept_ids,
                    empleadocargo__fecha_fin__isnull=True
                ).distinct()
            else:
                empleados = Empleado.objects.filter(id=user_empleado.id)

        # Crear registros de ausencia para los que no tienen hoy
        for e in empleados:
            if not HistorialAsistencia.objects.filter(empleado=e, fecha_asistencia=hoy).exists():
                HistorialAsistencia.objects.create(
                    empleado=e,
                    fecha_asistencia=hoy,
                    hora_entrada=None,
                    hora_salida=None,
                    tardanza=False,
                    confirmado=False
                )
                actualizados += 1

        messages.success(request, f"Se registraron {actualizados} ausentes de hoy.")
        return redirect("confirmar_asistencias")

    
    for aid in ids:
        asistencia = HistorialAsistencia.objects.filter(id=aid, fecha_asistencia=hoy).first()
        if not asistencia or asistencia.hora_entrada is None:
            continue

        if accion == "confirmar":
            if not asistencia.confirmado:
                asistencia.confirmado = True
                asistencia.save()
                actualizados += 1
        
        elif accion == "tardanza":
            if not asistencia.tardanza:
                asistencia.tardanza = True
                asistencia.confirmado = True
                asistencia.save()
                actualizados += 1

    if accion == "confirmar":
        messages.success(request, f"Se confirmaron {actualizados} asistencias.")
    elif accion == "tardanza":
        messages.warning(request, f"Se marcaron {actualizados} asistencias con tardanza.")

    return redirect("confirmar_asistencias")
