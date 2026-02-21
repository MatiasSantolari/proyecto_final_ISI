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
from django.core.paginator import Paginator


@login_required
def instituciones(request):
    form = InstitucionForm()
    institucionesList = Institucion.objects.all().order_by('nombre')

    paginator = Paginator(institucionesList, 15)
    page_number = request.GET.get('page')
    instituciones = paginator.get_page(page_number)

    return render(request, 'instituciones.html', {
        'form': form,
        'instituciones': instituciones
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
            nueva_inst = form.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'id': nueva_inst.id,
                    'nombre': nueva_inst.nombre,
                    'mensaje': "Institución guardada correctamente."
                })

            if id_institucion:
                messages.success(request, "La institucion se actualizó correctamente.")
            else:
                messages.success(request, "La institucion se creó correctamente.")
            return redirect('instituciones')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
            messages.error(request, "Hubo un error al guardar la institucion.")

    else:
        form = InstitucionForm()

    institucionesList = Institucion.objects.all()
    return render(request, 'instituciones.html', {'form': form, 'instituciones': institucionesList})



@login_required
@require_POST
def eliminar_institucion(request, id_institucion):
    try:
        institucion = get_object_or_404(Institucion, id=id_institucion)
        institucion.delete()
        messages.success(request, "institucion eliminada correctamente.")
    except Institucion.DoesNotExist:
        messages.error(request, "La institucion no existe.")
    return redirect('instituciones')