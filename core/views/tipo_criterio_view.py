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
def tiposCriterios(request):
    form = TipoCriterioForm()
    tiposCriteriosList = TipoCriterio.objects.all().order_by('descripcion')

    paginator = Paginator(tiposCriteriosList, 15)
    page_number = request.GET.get('page')
    tiposCriterios = paginator.get_page(page_number)

    return render(request, 'tipos_criterios.html', {
        'form': form,
        'tiposCriterios': tiposCriterios
    })


@login_required
def crear_tipoCriterio(request):
    id_tipoCriterio = request.POST.get('id_tipoCriterio')

    if request.method == 'POST':
        if id_tipoCriterio:
            tipoCriterio = get_object_or_404(TipoCriterio, pk=id_tipoCriterio)
            form = TipoCriterioForm(request.POST, instance=tipoCriterio)
        else:
            form = TipoCriterioForm(request.POST)

        if form.is_valid():
            form.save()
            if id_tipoCriterio:
                messages.success(request, "El tipo de criterio se actualizó correctamente.")
            else:
                messages.success(request, "El tipo de criterio se creó correctamente.")
            return redirect('tiposCriterios')
        else:
            messages.error(request, "Hubo un error al guardar el tipo de criterio. Verifique los datos ingresados.")

    else:
        form = TipoCriterioForm()

    tiposCriteriosList = TipoCriterio.objects.all()
    return render(request, 'tipos_criterios.html', {
        'form': form, 
        'tiposCriterios': tiposCriteriosList
    })


@login_required
@require_POST
def eliminar_tipoCriterio(request, id_tipoCriterio):
    try:
        tipoCriterio = get_object_or_404(TipoCriterio, id=id_tipoCriterio)
#        Criterio.objects.filter(tipoCriterio=tipoCriterio).delete() # Elimina todas las relaciones de Criterios con este tipoCriterio
        tipoCriterio.delete()
        messages.success(request, "Tipo de criterio eliminado correctamente.")
    except TipoCriterio.DoesNotExist:
        messages.error(request, "El tipo de criterio no existe.")
    return redirect('tiposCriterios')