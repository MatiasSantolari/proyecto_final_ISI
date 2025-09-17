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
def beneficios(request):
    form = BeneficioForm()
    beneficiosList = Beneficio.objects.all()

    for b in beneficiosList:
        if b.descripcion:
            b.descripcion = b.descripcion.capitalize()

    paginator = Paginator(beneficiosList, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'beneficios.html', {
        'form': form,
        'beneficios': page_obj,
    })


@login_required
@require_POST
def crear_beneficio(request):
    id_beneficio = request.POST.get('id_beneficio')

    if request.method == 'POST':
        if id_beneficio:
            beneficio = get_object_or_404(Beneficio, pk=id_beneficio)
            form = BeneficioForm(request.POST, instance=beneficio)
        else:
            form = BeneficioForm(request.POST)

        if form.is_valid():
            form.save()
            if id_beneficio:
                messages.success(request, "El beneficio se actualizó correctamente.")
            else:
                messages.success(request, "El beneficio se creó correctamente.")
            return redirect('beneficios')
        else:
            messages.error(request, "Hubo un error al guardar el beneficio. Verifique los datos ingresados.")

    else:
        form = BeneficioForm()

    beneficiosList = Beneficio.objects.all()
    return render(request, 'beneficios.html', {
        'form': form,
        'beneficios': beneficiosList
    })


@login_required
@require_POST
def activar_beneficio(request, id_beneficio):
    try:
        beneficio = get_object_or_404(Beneficio, id=id_beneficio)
        beneficio.activo = True
        beneficio.save()
        messages.success(request, "Beneficio activado correctamente.")
    except Beneficio.DoesNotExist:
        messages.error(request, "El beneficio no existe.")
    return redirect('beneficios')


@login_required
@require_POST
def desactivar_beneficio(request, id_beneficio):
    try:
        beneficio = get_object_or_404(Beneficio, id=id_beneficio)
        beneficio.activo = False
        beneficio.save()
        messages.success(request, "beneficio desactivado correctamente.")
    except Beneficio.DoesNotExist:
        messages.error(request, "El beneficio no existe.")
    return redirect('beneficios')


@login_required
@require_POST
def eliminar_beneficio(request, id_beneficio):
    try:
        beneficio = get_object_or_404(Beneficio, id=id_beneficio)
        beneficio.delete()
        messages.success(request, "Beneficio eliminado correctamente.")
    except Beneficio.DoesNotExist:
        messages.error(request, "El beneficio no existe.")
    return redirect('beneficios')
