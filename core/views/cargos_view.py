from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


@login_required
def cargos(request):
    cargos_con_sueldo = []

    departamento_seleccionado = request.GET.get('departamento', 'todos')

    relaciones = CargoDepartamento.objects.select_related('cargo', 'departamento').order_by('departamento__nombre', 'cargo__nombre')

    if departamento_seleccionado != 'todos':
        relaciones = relaciones.filter(departamento_id=departamento_seleccionado)

    for relacion in relaciones:
        cargo = relacion.cargo
        departamento = relacion.departamento

        ultimo_sueldo = HistorialSueldoBase.objects.filter(cargo=cargo).order_by('-fecha_sueldo').first()
        sueldo = ultimo_sueldo.sueldo_base if ultimo_sueldo else None

        cargos_con_sueldo.append({
            'id': cargo.id,
            'nombre': cargo.nombre,
            'descripcion': cargo.descripcion,
            'sueldo_base': sueldo,
            'departamento_id': departamento.id,
            'departamento': departamento.nombre,
            'vacante': relacion.vacante
        })

    paginator = Paginator(cargos_con_sueldo, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    departamentos = Departamento.objects.order_by('nombre')

    form = CargoForm()
    return render(request, 'cargos.html', {
        'cargos': page_obj, 
        'page_obj': page_obj,
        'form': form,
        'departamentos': departamentos,
        'departamento_seleccionado': departamento_seleccionado
        })



@login_required
@require_POST
def crear_cargo(request):
    if request.method == 'POST':
        id_cargo = request.POST.get('id_cargo')
        
        if id_cargo:
            cargo = get_object_or_404(Cargo, pk=id_cargo)
            form = CargoForm(request.POST, instance=cargo)
        else:
            form = CargoForm(request.POST)
        if form.is_valid():
            cargo_guardado = form.save()
            sueldo_base = form.cleaned_data['sueldo_base']

            departamento = form.cleaned_data['departamento']
            vacante = form.cleaned_data['vacante']

            CargoDepartamento.objects.update_or_create(
                cargo=cargo_guardado,
                departamento=departamento,
                defaults={'vacante': vacante}
            )

            ultimo_sueldo = HistorialSueldoBase.objects.filter(cargo=cargo_guardado).order_by('-fecha_sueldo').first()
            if not ultimo_sueldo or ultimo_sueldo.sueldo_base != sueldo_base:
                HistorialSueldoBase.objects.create(
                    cargo=cargo_guardado,
                    sueldo_base=sueldo_base,
                    fecha_sueldo=timezone.now()
                )

            return redirect('cargos')
    else:
        form = CargoForm(instance=cargo)

    cargos_con_sueldo = []
    cargos = Cargo.objects.all()

    for cargo in cargos:
        cargo_departamento = CargoDepartamento.objects.filter(cargo=cargo).first()
        departamento = cargo_departamento.departamento.nombre if cargo_departamento else 'Sin asignar'
        vacante = cargo_departamento.vacante if cargo_departamento else 0

        ultimo_sueldo = HistorialSueldoBase.objects.filter(cargo=cargo).order_by('-fecha_sueldo').first()
        sueldo = ultimo_sueldo.sueldo_base if ultimo_sueldo else None

        cargos_con_sueldo.append({
            'id': cargo.id,
            'nombre': cargo.nombre,
            'descripcion': cargo.descripcion,
            'sueldo_base': sueldo,
            'departamento': departamento,
            'vacante': vacante
        })

    return render(request, 'cargos.html', {'form': form, 'cargos': cargos_con_sueldo})


@login_required
@require_POST
def eliminar_cargo(request, id_cargo):
    cargo = get_object_or_404(Cargo, id=id_cargo)
    cargo.delete()
    return redirect('cargos')
