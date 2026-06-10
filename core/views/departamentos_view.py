import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from datetime import date
from django.views.decorators.http import require_POST
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from collections import defaultdict
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Case, When, IntegerField


@login_required
def departamentos(request):
    form = DepartamentoForm()
    
    orden_activos = Case(
        When(activo=False, then=2),
        default=1,
        output_field=IntegerField(),
    )

    departamentosList = (
        Departamento.objects.all()
        .annotate(prioridad_activo=orden_activos)
        .order_by('prioridad_activo', 'nombre')
    )

    paginator = Paginator(departamentosList, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'departamentos.html', {
        'form': form,
        'departamentos': page_obj,
    })


@login_required
@require_POST
def crear_departamento(request):
    id_departamento = request.POST.get('id_departamento')

    if request.method == 'POST':
        if id_departamento:
            departamento = get_object_or_404(Departamento, pk=id_departamento)
            form = DepartamentoForm(request.POST, instance=departamento)
        else:
            form = DepartamentoForm(request.POST)

        if form.is_valid():
            nuevo_departamento = form.save()

            if not id_departamento:
                cargos_info = [
                    ('Jefe de ' + nuevo_departamento.nombre, True, False),
                    ('Gerente de ' + nuevo_departamento.nombre, False, True),
                ]

                for nombre_cargo, es_jefe, es_gerente in cargos_info:
                    cargo = Cargo.objects.create(
                        nombre=nombre_cargo,
                        descripcion=f"",
                        es_jefe=es_jefe,
                        es_gerente=es_gerente
                    )

                    CargoDepartamento.objects.create(
                        cargo=cargo,
                        departamento=nuevo_departamento,
                        vacante=1
                    )

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'id': nuevo_departamento.id,
                        'nombre': nuevo_departamento.nombre
                    })

                messages.success(request, f"Departamento '{nuevo_departamento.nombre}' creado correctamente.")
            else:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'id': nuevo_departamento.id,
                        'nombre': nuevo_departamento.nombre
                    })

                messages.success(request, f"Departamento '{nuevo_departamento.nombre}' actualizado correctamente.")

            return redirect('departamentos')
        
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'errors': form.errors
                }, status=400)
            
    else:
        form = DepartamentoForm()

    messages.error(request, "Hubo un error al guardar el departamento. Verifica los datos.")
    
    orden_activos = Case(When(activo=False, then=2), default=1, output_field=IntegerField())
    departamentosList = Departamento.objects.all().annotate(prioridad_activo=orden_activos).order_by('prioridad_activo', 'nombre')
    
    return render(request, 'departamentos.html', {'form': form, 'departamentos': departamentosList})



@login_required
@require_POST
def eliminar_departamento(request, id_departamento):
    departamento = get_object_or_404(Departamento, id=id_departamento)
    
    departamento.activo = False
    departamento.save()
    
    messages.success(request, f"El departamento '{departamento.nombre}' ha sido desactivado correctamente.")
    return redirect('departamentos')



@login_required
@require_POST
def reactivar_departamento(request, id_departamento):
    departamento = get_object_or_404(Departamento, id=id_departamento)
    departamento.activo = True
    departamento.save()
    
    messages.success(request, f"El departamento '{departamento.nombre}' ha sido reactivado correctamente.")
    return redirect('departamentos')