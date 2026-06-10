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
    orden_tipos_activos = Case(
        When(tipo_criterio__activo=False, then=2),
        default=1,
        output_field=IntegerField(),
    )

    orden_criterios_activos = Case(
        When(activo=False, then=2),
        default=1,
        output_field=IntegerField(),
    )

    criterios_list = (
        Criterio.objects.select_related('tipo_criterio')
        .annotate(
            prioridad_tipo=orden_tipos_activos,
            prioridad_criterio=orden_criterios_activos
        )
        .order_by(
            'prioridad_tipo', 
            'tipo_criterio__descripcion', 
            'prioridad_criterio', 
            'descripcion'
        )
    )
    
    paginator = Paginator(criterios_list, 15)
    page_number = request.GET.get('page')
    criterios_page = paginator.get_page(page_number)

    form = CriterioForm()

    return render(request, 'criterios.html', {
        'criterios': criterios_page,
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



@login_required
@require_POST
def eliminar_criterio(request, id):
    criterio = get_object_or_404(Criterio, pk=id)
    criterio.activo = False
    criterio.save()
    messages.success(request, f"El criterio '{criterio.descripcion}' ha sido desactivado correctamente.")
    return redirect('criterios')


@login_required
@require_POST
def reactivar_criterio(request, id):
    criterio = get_object_or_404(Criterio, pk=id)
    criterio.activo = True
    criterio.save()
    messages.success(request, f"El criterio '{criterio.descripcion}' ha sido reactivado correctamente.")
    return redirect('criterios')
