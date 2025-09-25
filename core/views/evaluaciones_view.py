from django.http import JsonResponse
from ..models import *
from ..forms import *
from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from collections import defaultdict
from django.template.loader import render_to_string
from django.core.paginator import Paginator


@login_required
def evaluaciones(request):
    evaluaciones = Evaluacion.objects.prefetch_related('evaluacioncriterio_set__criterio__tipo_criterio').order_by('-fecha_evaluacion')   
    tipos_criterio = TipoCriterio.objects.prefetch_related('criterio_set').all()
    form = EvaluacionForm()
    return render(request, 'evaluaciones.html', {
        'evaluaciones': evaluaciones,
        'tipos_criterio': tipos_criterio,
        'form': form
    })



@login_required
@require_POST
def crear_evaluacion(request):
    id_evaluacion = request.POST.get('id_evaluacion')
    if id_evaluacion:
        evaluacion = get_object_or_404(Evaluacion, pk=id_evaluacion)
        form = EvaluacionForm(request.POST, instance=evaluacion)
    else:
        form = EvaluacionForm(request.POST)

    if form.is_valid():
        evaluacion = form.save()

        criterios_ids = request.POST.getlist('criterio')
        ponderaciones = request.POST.getlist('ponderacion')

        EvaluacionCriterio.objects.filter(evaluacion=evaluacion).delete()

        tipo_dict = {}
        for idx, c_id in enumerate(criterios_ids):
            c = get_object_or_404(Criterio, pk=c_id)
            p = float(ponderaciones[idx])
            if p < 0 or p > 1:
                messages.error(request, f"La ponderación del criterio {c.descripcion} debe estar entre 0 y 1")
                return redirect('evaluaciones')

            EvaluacionCriterio.objects.create(evaluacion=evaluacion, criterio=c, ponderacion=p)
            tipo_dict.setdefault(c.tipo_criterio.id, 0)
            tipo_dict[c.tipo_criterio.id] += p

        for tipo_id, suma in tipo_dict.items():
            if round(suma, 2) != 1:
                tipo = TipoCriterio.objects.get(pk=tipo_id)
                messages.error(request, f"La suma de ponderaciones del tipo '{tipo.descripcion}' debe ser 1. Actualmente es {suma}")
                return redirect('evaluaciones')

        if id_evaluacion:
            messages.success(request, "Evaluación actualizada correctamente")
        else:
            messages.success(request, "Evaluación creada correctamente")
    else:
        messages.error(request, "Error en el formulario de evaluación")

    return redirect('evaluaciones')




@login_required
def ver_evaluacion(request, id_evaluacion):
    evaluacion = get_object_or_404(Evaluacion, id=id_evaluacion)

    tipos_dict = defaultdict(list)
    for ec in evaluacion.evaluacioncriterio_set.all():
        tipo_desc = ec.criterio.tipo_criterio.descripcion
        tipos_dict[tipo_desc].append({
            "id": ec.criterio.id,
            "descripcion": ec.criterio.descripcion,
            "ponderacion": ec.ponderacion
        })

    data = {
        "id": evaluacion.id,
        "descripcion": evaluacion.descripcion,
        "fecha_evaluacion": evaluacion.fecha_evaluacion.strftime("%d/%m/%Y"),
        "activo": evaluacion.activo,
        "tipos": tipos_dict
    }
    return JsonResponse(data)



@login_required
@require_POST
def activar_evaluacion(request, id_evaluacion):
    evaluacion = get_object_or_404(Evaluacion, pk=id_evaluacion)
    evaluacion.activo = True
    evaluacion.save()
    messages.success(request, "Evaluación activada")
    return redirect('evaluaciones')



@login_required
@require_POST
def desactivar_evaluacion(request, id_evaluacion):
    evaluacion = get_object_or_404(Evaluacion, pk=id_evaluacion)
    evaluacion.activo = False
    evaluacion.save()
    messages.success(request, "Evaluación desactivada")
    return redirect('evaluaciones')



@login_required
@require_POST
def eliminar_evaluacion(request, id_evaluacion):
    evaluacion = get_object_or_404(Evaluacion, pk=id_evaluacion)
    evaluacion.delete()
    messages.success(request, "Evaluación eliminada")
    return redirect('evaluaciones')



@login_required
def evaluacion_json(request, evaluacion_id):
    eval = get_object_or_404(Evaluacion, id=evaluacion_id)
    tipos = []
    for tipo in eval.evaluacioncriterio_set.values('criterio__tipo_criterio', 'criterio__tipo_criterio__descripcion').distinct():
        criterios = eval.evaluacioncriterio_set.filter(criterio__tipo_criterio=tipo['criterio__tipo_criterio'])
        tipos.append({
            'descripcion': tipo['criterio__tipo_criterio__descripcion'],
            'criterios': [{'id': c.criterio.id, 'descripcion': c.criterio.descripcion, 'ponderacion': c.ponderacion} for c in criterios]
        })
    return JsonResponse(tipos, safe=False)


############


def gestionar_empleados(request, id_evaluacion):
    evaluacion = get_object_or_404(Evaluacion, id=id_evaluacion)
    departamentos = Departamento.objects.order_by('nombre')
    departamento_seleccionado = request.GET.get('departamento', 'todos')
    dni = request.GET.get('dni', '').strip()
    empleados = Empleado.objects.all().distinct().order_by('apellido','nombre')

    if departamento_seleccionado != 'todos':
        empleados = empleados.filter(
            empleadocargo__fecha_fin__isnull=True,
            empleadocargo__cargo__cargodepartamento__departamento__id=departamento_seleccionado
        )
    if dni:
        empleados = empleados.filter(dni__icontains=dni)

    empleados = empleados.distinct()

    asignados_ids = EvaluacionEmpleado.objects.filter(
        evaluacion=evaluacion
    ).values_list('empleado_id', flat=True)

    paginator = Paginator(empleados, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'evaluacion_empleados.html', {
        'evaluacion': evaluacion,
        'departamentos': departamentos,
        'empleados': page_obj,
        'page_obj': page_obj,
        'asignados_ids': asignados_ids,
        'departamento_seleccionado': str(departamento_seleccionado),
        'dni_busqueda': dni,
    })



@login_required
def asignar_empleado(request, id_evaluacion, id_empleado):
    evaluacion = get_object_or_404(Evaluacion, pk=id_evaluacion)
    empleado = get_object_or_404(Empleado, pk=id_empleado)

    EvaluacionEmpleado.objects.get_or_create(
        evaluacion=evaluacion,
        empleado=empleado,
        fecha_registro=date.today()
    )
    messages.success(request, f"Empleado {empleado} asignado a la evaluación.")

    departamento = request.GET.get('departamento', 'todos')
    dni = request.GET.get('dni', '')

    return redirect(f'/evaluaciones/{id_evaluacion}/empleados/?departamento={departamento}&dni={dni}')



@login_required
def quitar_empleado(request, id_evaluacion, id_empleado):
    evaluacion = get_object_or_404(Evaluacion, pk=id_evaluacion)
    empleado = get_object_or_404(Empleado, pk=id_empleado)

    EvaluacionEmpleado.objects.filter(
        evaluacion=evaluacion,
        empleado=empleado
    ).delete()

    messages.success(request, f"Empleado {empleado} quitado de la evaluación.")

    departamento = request.GET.get('departamento', 'todos')
    dni = request.GET.get('dni', '')

    return redirect(f'/evaluaciones/{id_evaluacion}/empleados/?departamento={departamento}&dni={dni}')
