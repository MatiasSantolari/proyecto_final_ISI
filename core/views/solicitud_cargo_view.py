import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone


@login_required
def solicitar_cargos(request):
    empleado = request.user.persona.empleado
    departamento = empleado.departamento_actual()
    
    if not departamento:
        messages.error(request, "No se pudo determinar tu departamento.")
        return redirect('home')

    solicitudes_list = SolicitudCargo.objects.filter(
        departamento=departamento
    ).select_related('solicitante__persona', 'cargo_existente').order_by('-fecha_solicitud')
    
    paginator = Paginator(solicitudes_list, 10)
    page = request.GET.get('page')
    solicitudes = paginator.get_page(page)

    cargos_depto = Cargo.objects.filter(cargodepartamento__departamento=departamento).distinct()

    return render(request, 'solicitar_cargos.html', {
        'solicitudes': solicitudes,
        'cargos': cargos_depto,
        'departamento': departamento
    })



@login_required
def crear_solicitud(request):
    if request.method == 'POST':
        empleado = request.user.persona.empleado
        departamento = empleado.departamento_actual()
        
        tipo = request.POST.get('tipo')
        try:
            solicitud = SolicitudCargo(
                solicitante=request.user,
                departamento=departamento,
                tipo=tipo,
                cupos=int(request.POST.get('cupos', 1)),
                perfil_detallado=request.POST.get('perfil_detallado')
            )
            
            if tipo == 'EXISTENTE':
                solicitud.cargo_existente_id = request.POST.get('cargo_existente')
            else:
                solicitud.nombre_cargo_nuevo = request.POST.get('nombre_nuevo')
                solicitud.descripcion_cargo_nuevo = request.POST.get('desc_nuevo')
            
            solicitud.save()
            messages.success(request, "Solicitud enviada correctamente al administrador.")
        except Exception as e:
            messages.error(request, f"Error al procesar la solicitud: {e}")
            
    return redirect('solicitar_cargos')




@login_required
def gestion_solicitudes(request):
    if request.user.rol != 'admin':
        return redirect('home')

    solicitudes_list = SolicitudCargo.objects.all().select_related(
        'solicitante__persona', 'departamento', 'cargo_existente'
    ).order_by('-fecha_solicitud')
    
    paginator = Paginator(solicitudes_list, 10)
    page = request.GET.get('page')
    solicitudes = paginator.get_page(page)

    return render(request, 'gestion_solicitudes_cargos.html', {'solicitudes': solicitudes})

@login_required
def aprobar_solicitud(request, id_solicitud):
    solicitud = get_object_or_404(SolicitudCargo, id=id_solicitud)
    solicitud.estado = 'APROBADA'
    solicitud.save()
    messages.success(request, f"Solicitud #{id_solicitud} aprobada correctamente.")
    return redirect('gestion_solicitudes')

@login_required
def rechazar_solicitud(request, id_solicitud):
    if request.method == 'POST':
        solicitud = get_object_or_404(SolicitudCargo, id=id_solicitud)
        motivo = request.POST.get('motivo_admin')
        
        if not motivo:
            messages.error(request, "Debe especificar un motivo para el rechazo.")
        else:
            solicitud.estado = 'RECHAZADA'
            solicitud.motivo_admin = motivo
            solicitud.save()
            messages.warning(request, f"Solicitud #{id_solicitud} rechazada.")
            
    return redirect('gestion_solicitudes')




@login_required
def aprobar_solicitud(request, id_solicitud):
    if request.user.rol != 'admin':
        return redirect('home')

    solicitud = get_object_or_404(SolicitudCargo, id=id_solicitud)
    
    sueldo_input = request.POST.get('sueldo_base')
    sueldo_final = float(sueldo_input) if sueldo_input and sueldo_input.strip() else 0.0

    if solicitud.tipo == 'EXISTENTE':
        relacion = CargoDepartamento.objects.filter(
            cargo=solicitud.cargo_existente, 
            departamento=solicitud.departamento
        ).first()

        if relacion:
            relacion.vacante += solicitud.cupos
            relacion.save()
            solicitud.estado = 'APROBADA'
            solicitud.save()
            messages.success(request, f"Se sumaron {solicitud.cupos} vacantes a {solicitud.cargo_existente.nombre}")
        else:
            messages.error(request, "Error: El cargo existe pero no tiene relación con el departamento.")

    else:
        try:
            nuevo_cargo = Cargo.objects.create(
                nombre=solicitud.nombre_cargo_nuevo,
                descripcion=solicitud.descripcion_cargo_nuevo,
                es_jefe=False,
                es_gerente=False
            )

            CargoDepartamento.objects.create(
                cargo=nuevo_cargo,
                departamento=solicitud.departamento,
                vacante=solicitud.cupos
            )

            HistorialSueldoBase.objects.create(
                cargo=nuevo_cargo,
                sueldo_base=sueldo_final,
                fecha_sueldo=timezone.now()
            )

            solicitud.estado = 'APROBADA'
            solicitud.save()
            messages.success(request, f"Cargo '{nuevo_cargo.nombre}' creado y aprobado con éxito.")
        
        except Exception as e:
            messages.error(request, f"Error crítico al crear el cargo: {e}")

    return redirect('gestion_solicitudes')
