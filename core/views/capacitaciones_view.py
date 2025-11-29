from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

@login_required
def capacitaciones(request):
    lista_capacitaciones = []

    relaciones = InstitucionCapacitacion.objects.select_related('institucion', 'capacitacion').order_by('institucion__nombre', 'capacitacion__nombre')

    for relacion in relaciones:
        institucion = relacion.institucion
        capacitacion = relacion.capacitacion

        lista_capacitaciones.append({
            'id': capacitacion.id,
            'nombre': capacitacion.nombre,
            'descripcion': capacitacion.descripcion,
            'fecha_inicio': capacitacion.fecha_inicio,
            'fecha_fin': capacitacion.fecha_fin,
            'origen_org': capacitacion.origen_org,
            'presencial': capacitacion.presencial,
            'cupo': capacitacion.cupo,
            'institucion_id': institucion.id,
            'institucion': institucion.nombre,
        })

    paginator = Paginator(lista_capacitaciones, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    instituciones = Institucion.objects.order_by('nombre')

    form = CapacitacionForm()
    return render(request, 'capacitaciones.html', {
        'capacitaciones': page_obj, 
        'page_obj': page_obj,
        'form': form,
        #'instituciones': instituciones,
        #'institucion_seleccionada': institucion_seleccionada -----> para luego agregar un filtro si pinta
        })

@login_required
@require_POST
def crear_capacitacion(request):
    if request.method == 'POST':
        id_capacitacion = request.POST.get('id_capacitacion')
        
        if id_capacitacion:
            capacitacion = get_object_or_404(Capacitacion, pk=id_capacitacion)
            form = CapacitacionForm(request.POST, instance=capacitacion)
        else:
            form = CapacitacionForm(request.POST)
        if form.is_valid():
            capacitacion_guardada = form.save()
            institucion = form.cleaned_data['institucion']

            InstitucionCapacitacion.objects.update_or_create(
                capacitacion=capacitacion_guardada,
                institucion=institucion
            )

            return redirect('capacitaciones')
    else:
        form = CapacitacionForm(instance=capacitacion)

    lista_capacitaciones = []
    capacitaciones = Capacitacion.objects.all()

    for capacitacion in capacitaciones:
        capacitacion_institucion = InstitucionCapacitacion.objects.filter(capacitacion=capacitacion).first()
        institucion = capacitacion_institucion.institucion.nombre if capacitacion_institucion else 'Sin asignar'

        lista_capacitaciones.append({
            'id': capacitacion.id,
            'nombre': capacitacion.nombre,
            'descripcion': capacitacion.descripcion,
            'fecha_inicio': capacitacion.fecha_inicio,
            'fecha_fin': capacitacion.fecha_fin,
            'institucion': institucion,
        })

    return render(request, 'capacitaciones.html', {'form': form, 'capacitaciones': lista_capacitaciones})


@login_required
@require_POST
def eliminar_capacitacion(request, id_capacitacion):
    capacitacion = get_object_or_404(Cargo, id=id_capacitacion)
    capacitacion.delete()
    return redirect('capacitaciones')
