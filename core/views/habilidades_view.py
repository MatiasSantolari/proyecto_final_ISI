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
def habilidades(request):
    form = HabilidadForm()
    
    orden_activos = Case(
        When(activo=False, then=2),
        default=1,
        output_field=IntegerField(),
    )

    habilidadesList = (
        Habilidad.objects.all()
        .annotate(prioridad_activo=orden_activos)
        .order_by('prioridad_activo', 'nombre')
    )

    paginator = Paginator(habilidadesList, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'habilidades.html', {
        'form': form,
        'habilidades': page_obj
    })



@login_required
def crear_habilidad(request):
    id_habilidad = request.POST.get('id_habilidad')

    if request.method == 'POST':
        if id_habilidad:
            habilidad = get_object_or_404(Habilidad, pk=id_habilidad)
            form = HabilidadForm(request.POST, instance=habilidad)
        else:
            form = HabilidadForm(request.POST)

        if form.is_valid():
            form.save()
            if id_habilidad:
                messages.success(request, "La habilidad se actualizó correctamente.")
            else:
                messages.success(request, "La habilidad se creó correctamente.")
            return redirect('habilidades')
        else:
            messages.error(request, "Hubo un error al guardar la habilidad. Verifique los datos ingresados.")

    else:
        form = HabilidadForm()

    habilidadesList = Habilidad.objects.all()
    return render(request, 'habilidades.html', {'form': form, 'habilidades': habilidadesList})


@login_required
@require_POST
def eliminar_habilidad(request, id_habilidad):
    habilidad = get_object_or_404(Habilidad, id=id_habilidad)
    habilidad.activo = False
    habilidad.save()
    
    messages.success(request, f"La habilidad '{habilidad.nombre}' ha sido desactivada correctamente.")
    return redirect('habilidades')


@login_required
@require_POST
def reactivar_habilidad(request, id_habilidad):
    habilidad = get_object_or_404(Habilidad, id=id_habilidad)
    habilidad.activo = True
    habilidad.save()
    
    messages.success(request, f"La habilidad '{habilidad.nombre}' ha sido reactivada correctamente.")
    return redirect('habilidades')
