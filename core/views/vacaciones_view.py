from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, Value, IntegerField



@login_required
def solicitar_vacaciones(request):
    empleado = get_object_or_404(Empleado, usuario=request.user)
    solicitudes = (
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
        solicitudes = (VacacionesSolicitud.objects
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
        solicitudes = (VacacionesSolicitud.objects
                        .filter(empleado__empleadocargo__cargo__cargodepartamento__departamento=departamento)
                        .exclude(estado="cancelado")
                        .order_by("-fecha_solicitud")
        )

    return render(request, "vacaciones_gestionar.html", {
        "solicitudes": solicitudes
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

