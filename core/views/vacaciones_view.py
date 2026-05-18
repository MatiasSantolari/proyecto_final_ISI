import csv
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, Value, IntegerField, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ..models import *
from ..forms import *


@login_required
def solicitar_vacaciones(request):
    empleado = get_object_or_404(Empleado, usuario=request.user)
    solicitudes_list = (
        VacacionesSolicitud.objects
        .filter(empleado=empleado)
        .annotate(
            estado_prioridad=Case(
                When(estado="pendiente", then=Value(1)),
                When(estado="aprobado", then=Value(2)),
                When(estado="rechazado", then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            )
        )
        .order_by("-fecha_solicitud", "fecha_inicio", "estado_prioridad")
    )

    paginator = Paginator(solicitudes_list, 10)
    page_number = request.GET.get("page", 1)
    
    try:
        solicitudes = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        solicitudes = paginator.page(1)

    rango_paginas = list(paginator.get_elided_page_range(
        solicitudes.number, 
        on_each_side=2, 
        on_ends=1
    ))

    if request.method == "POST":
        form = VacacionesSolicitudForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.empleado = empleado
            solicitud.cant_dias_solicitados = form.cleaned_data.get("cant_dias_solicitados", 0)
            solicitud.save()
            messages.success(request, "Solicitud enviada correctamente.")
            return redirect("solicitar_vacaciones")
        else:
            messages.error(request, "No se pudo completar la solicitud. Verifica los datos ingresados.")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = VacacionesSolicitudForm()

    return render(request, "vacaciones_solicitar.html", {
        "form": form,
        "solicitudes": solicitudes,
        "rango_paginas": rango_paginas,
        "dias_disponibles": empleado.cantidad_dias_disponibles
    })


@login_required
def gestionar_vacaciones(request):
    user = request.user
    try:
        rol = Empleado.objects.get(pk=user.persona.id)
    except Empleado.DoesNotExist:
        messages.error(request, "No se encontró un empleado asociado a este usuario.")
        return redirect("home")

    departamento = rol.departamento_actual()

    if user.rol == "admin":
        solicitudes_list = (VacacionesSolicitud.objects
            .exclude(estado="cancelado")
            .annotate(
                estado_prioridad=Case(
                    When(estado="pendiente", then=Value(1)),
                    When(estado="aprobado", then=Value(2)),
                    When(estado="rechazado", then=Value(3)),
                    default=Value(4),
                    output_field=IntegerField(),
                )
            )
            .order_by("-fecha_solicitud", "fecha_inicio", "estado_prioridad")
        )
    else:
        empleado = get_object_or_404(Empleado, usuario=user)
        solicitudes_list = (VacacionesSolicitud.objects
                        .filter(empleado__empleadocargo__cargo__cargodepartamento__departamento=departamento)
                        .exclude(estado="cancelado")
                        .order_by("-fecha_solicitud")
        )

    nombre_query = request.GET.get('nombre')
    depto_query = request.GET.get('departamento_id')
    estado_query = request.GET.get('estado')

    if nombre_query and nombre_query.strip():
        solicitudes_list = solicitudes_list.filter(
            Q(empleado__nombre__icontains=nombre_query) | Q(empleado__apellido__icontains=nombre_query)
        )
    if depto_query and depto_query.strip():
        solicitudes_list = solicitudes_list.filter(
            empleado__empleadocargo__fecha_fin__isnull=True,
            empleado__empleadocargo__cargo__cargodepartamento__departamento_id=depto_query
        )
    if estado_query and estado_query.strip():
        solicitudes_list = solicitudes_list.filter(estado=estado_query)

    solicitudes_list = solicitudes_list.distinct()

    paginator = Paginator(solicitudes_list, 10)
    page_number = request.GET.get("page", 1)
    
    try:
        solicitudes = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        solicitudes = paginator.page(1)

    rango_paginas = list(paginator.get_elided_page_range(
        solicitudes.number, 
        on_each_side=2, 
        on_ends=1
    ))

    todos_departamentos = Departamento.objects.all().order_by('nombre')

    return render(request, "vacaciones_gestionar.html", {
        "solicitudes": solicitudes,
        "rango_paginas": rango_paginas,
        "departamentos": todos_departamentos
    })


@login_required
def cambiar_estado_vacacion(request, pk, accion):
    solicitud = get_object_or_404(VacacionesSolicitud, pk=pk)
    empleado = solicitud.empleado

    if accion == "aprobar" and solicitud.estado == "pendiente":
        solicitud.estado = "aprobado"
        
        if solicitud.cant_dias_solicitados <= empleado.cantidad_dias_disponibles:
            empleado.cantidad_dias_disponibles -= solicitud.cant_dias_solicitados
        else:
            empleado.cantidad_dias_disponibles = 0

        empleado.save()

    elif accion == "rechazar" and solicitud.estado == "pendiente":
        solicitud.estado = "rechazado"
    
    solicitud.save()
    return redirect("gestionar_vacaciones")


@login_required
def cancelar_vacacion(request, pk):
    solicitud = get_object_or_404(VacacionesSolicitud, pk=pk, empleado__usuario=request.user)
    if solicitud.estado == "pendiente":  
        solicitud.estado = "cancelado"
        solicitud.save()
        messages.success(request, "Solicitud cancelada correctamente.")
    return redirect("solicitar_vacaciones")
