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

    orden_tipos_activos = Case(
        When(activo=False, then=2),
        default=1,
        output_field=IntegerField(),
    )

    tiposCriteriosList = (
        TipoCriterio.objects.all()
        .annotate(prioridad_activo=orden_tipos_activos)
        .order_by('prioridad_activo', 'descripcion')
    )

    paginator = Paginator(tiposCriteriosList, 15)
    page_number = request.GET.get('page')
    tiposCriterios_page = paginator.get_page(page_number)

    return render(request, 'tipos_criterios.html', {
        'form': form,
        'tiposCriterios': tiposCriterios_page
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
    tipoCriterio = get_object_or_404(TipoCriterio, id=id_tipoCriterio)
    tipoCriterio.activo = False
    tipoCriterio.save()
    messages.success(request, f"El tipo de criterio '{tipoCriterio.descripcion}' ha sido desactivado correctamente.")
    return redirect('tiposCriterios')


@login_required
@require_POST
def reactivar_tipoCriterio(request, id_tipoCriterio):
    tipoCriterio = get_object_or_404(TipoCriterio, id=id_tipoCriterio)
    tipoCriterio.activo = True
    tipoCriterio.save()
    messages.success(request, f"El tipo de criterio '{tipoCriterio.descripcion}' ha sido reactivado correctamente.")
    return redirect('tiposCriterios')
