import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required


@login_required
def instituciones(request):
    form = InstitucionForm()
    institucionesList = Institucion.objects.all()
    return render(request, 'instituciones.html', {
        'form': form,
        'instituciones': institucionesList
    })


@login_required
def crear_institucion(request):
    id_institucion = request.POST.get('id_institucion')

    if request.method == 'POST':
        if id_institucion:
            institucion = get_object_or_404(Institucion, pk=id_institucion)
            form = InstitucionForm(request.POST, instance=institucion)
        else:
            form = InstitucionForm(request.POST)

        if form.is_valid():
            form.save()
            if id_institucion:
                messages.success(request, "La institucion se actualizó correctamente.")
            else:
                messages.success(request, "La institucion se creó correctamente.")
            return redirect('instituciones')
        else:
            messages.error(request, "Hubo un error al guardar la institucion. Verifique los datos ingresados.")

    else:
        form = InstitucionForm()

    institucionesList = Institucion.objects.all()
    return render(request, 'instituciones.html', {'form': form, 'instituciones': institucionesList})


@login_required
@require_POST
def eliminar_institucion(request, id_institucion):
    try:
        institucion = get_object_or_404(Institucion, id=id_institucion)
        InstitucionCapacitacion.objects.filter(institucion=institucion).delete() # Elimina todas las relaciones de capacitaciones con esta institucion
        institucion.delete()
        messages.success(request, "institucion eliminada correctamente.")
    except Institucion.DoesNotExist:
        messages.error(request, "La institucion no existe.")
    return redirect('instituciones')