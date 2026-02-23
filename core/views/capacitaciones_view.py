from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages


@login_required
def capacitaciones(request):
    capacitaciones_list = Capacitacion.objects.all().order_by('-id')
    
    paginator = Paginator(capacitaciones_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = CapacitacionForm()
    form_inst = InstitucionForm() 

    return render(request, 'capacitaciones.html', {
        'form': form,
        'form_institucion': form_inst,
        'capacitaciones': page_obj
    })


@login_required
def guardar_capacitacion(request):
    id_capacitacion = request.POST.get('id_capacitacion')
    form_inst = InstitucionForm() 

    if request.method == 'POST':
        if id_capacitacion:
            instancia = get_object_or_404(Capacitacion, pk=id_capacitacion)
            form = CapacitacionForm(request.POST, request.FILES, instance=instancia)
        else:
            form = CapacitacionForm(request.POST, request.FILES)

        if form.is_valid():
            nueva_capacitacion = form.save(commit=False)
            if not id_capacitacion:
                nueva_capacitacion.activo = True
            nueva_capacitacion.save()     
            msg = "actualizó" if id_capacitacion else "creó"
            messages.success(request, f"La capacitación se {msg} correctamente.")
            return redirect('capacitaciones')
        else:
            capacitaciones_list = Capacitacion.objects.all().order_by('-id')
            return render(request, 'capacitaciones.html', {
                'form': form, 
                'form_institucion': form_inst,
                'capacitaciones': capacitaciones_list
            })
    return redirect('capacitaciones')


@login_required
@require_POST
def activar_capacitacion(request, id_cap):
    try:
        capacitacion = get_object_or_404(Capacitacion, id=id_cap)
        capacitacion.activo = True 
        capacitacion.save()
        messages.success(request, "Capacitación activada correctamente.")
    except Capacitacion.DoesNotExist:
        messages.error(request, "La capacitación no existe.")
    return redirect('capacitaciones')


@login_required
@require_POST
def desactivar_capacitacion(request, id_cap):
    try:
        capacitacion = get_object_or_404(Capacitacion, id=id_cap)
        capacitacion.activo = False 
        capacitacion.save()
        messages.success(request, "Capacitación desactivada correctamente.")
    except Capacitacion.DoesNotExist:
        messages.error(request, "La capacitación no existe.")
    return redirect('capacitaciones')


@login_required
@require_POST
def eliminar_capacitacion(request, id_cap):
    capacitacion = get_object_or_404(Capacitacion, id=id_cap)
    capacitacion.delete()
    messages.success(request, "Capacitación eliminada definitivamente.")
    return redirect('capacitaciones')



@login_required
def cartelera_capacitaciones(request):
    query = Capacitacion.objects.filter(activo=True).order_by('-fecha_creacion')
    
    mis_inscripciones = CapacitacionEmpleado.objects.filter(
        empleado__usuario=request.user
    ).values_list('capacitacion_id', flat=True)

    paginator = Paginator(query, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'capacitaciones_cartelera.html', {
        'capacitaciones': page_obj,
        'mis_inscripciones': mis_inscripciones,
    })



@login_required
def inscribir_capacitacion(request, cap_id):
    capacitacion = get_object_or_404(Capacitacion, id=cap_id)
    empleado = get_object_or_404(Empleado, usuario=request.user)

    inscripcion, created = CapacitacionEmpleado.objects.get_or_create(
        capacitacion=capacitacion,
        empleado=empleado,
        defaults={'estado': 'INSCRIPTO'}
    )

    if capacitacion.url_sitio:
        return redirect(capacitacion.url_sitio)

    if created:
        messages.success(request, f"Te has inscripto correctamente a: {capacitacion.nombre}")
    else:
        messages.info(request, "Ya te encuentras inscripto en esta capacitación.")

    return redirect('cartelera_capacitaciones')

