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


@require_POST
@login_required
def crear_tipoCriterio(request):
    id_tipoCriterio = request.POST.get('id_tipoCriterio')
    descripciones = request.POST.getlist('descripcion') 

    if id_tipoCriterio:
        tipoCriterio = get_object_or_404(TipoCriterio, pk=id_tipoCriterio)
        form = TipoCriterioForm(request.POST, instance=tipoCriterio)
        if form.is_valid():
            form.save()
            messages.success(request, "El tipo de criterio se actualizó correctamente.")
        else:
            messages.error(request, "Hubo un error al actualizar el tipo de criterio.")
    else:
        creados = 0
        for desc in descripciones:
            if desc.strip():
                TipoCriterio.objects.create(descripcion=desc.strip())
                creados += 1

        if creados > 0:
            messages.success(request, f"Se crearon {creados} tipos de criterios correctamente.")
        else:
            messages.error(request, "Debe ingresar al menos una descripción válida.")

    return redirect('tiposCriterios')


@login_required
@require_POST
def eliminar_tipoCriterio(request, id_tipoCriterio):
    try:
        tipoCriterio = get_object_or_404(TipoCriterio, id=id_tipoCriterio)
        tipoCriterio.delete()
        messages.success(request, "Tipo de criterio eliminado correctamente.")
    except TipoCriterio.DoesNotExist:
        messages.error(request, "El tipo de criterio no existe.")
    return redirect('tiposCriterios')