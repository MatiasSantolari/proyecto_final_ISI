from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator


@login_required
def criterios(request):
    criterios_list = Criterio.objects.select_related('tipo_criterio').all().order_by('tipo_criterio__descripcion')
    
    paginator = Paginator(criterios_list, 15)
    page_number = request.GET.get('page')
    criterios = paginator.get_page(page_number)

    form = CriterioForm()

    return render(request, 'criterios.html', {
        'criterios': criterios,
        'form': form
    })


@require_POST
@login_required
def crear_criterio(request):
    id_criterio = request.POST.get('id_criterio')

    if request.method == 'POST':
        if id_criterio:
            criterio = get_object_or_404(Criterio, pk=id_criterio)
            form = CriterioForm(request.POST, instance=criterio)
            if form.is_valid():
                form.save()
                messages.success(request, "El criterio se actualizó correctamente.")
                return redirect('criterios')
            else:
                messages.error(request, "Hubo un error al actualizar el criterio.")
        
        else:
            tipo_id = request.POST.get('tipo_criterio')
            descripciones = request.POST.getlist('descripciones[]')

            if not tipo_id:
                messages.error(request, "Debe seleccionar un tipo de criterio.")
                return redirect('criterios')

            if not descripciones or all(d.strip() == "" for d in descripciones):
                messages.error(request, "Debe ingresar al menos una descripción.")
                return redirect('criterios')

            tipo = get_object_or_404(TipoCriterio, pk=tipo_id)
            creados = 0
            for desc in descripciones:
                if desc.strip():
                    Criterio.objects.create(tipo_criterio=tipo, descripcion=desc.strip())
                    creados += 1

            messages.success(request, f"Se crearon {creados} criterios correctamente.")
            return redirect('criterios')

    return redirect('criterios')



@require_POST
@login_required
def eliminar_criterio(request, id):
    criterio = get_object_or_404(Criterio, pk=id)
    criterio.delete()
    messages.success(request, "El criterio fue eliminado correctamente.")
    return redirect('criterios')