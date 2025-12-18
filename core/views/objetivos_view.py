from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from datetime import date
from ..models import *
from ..forms import *


@login_required
def objetivos(request):
    user = request.user
    empleado_logueado = get_object_or_404(Empleado, id=user.persona.id)
    mi_depto = empleado_logueado.departamento_actual()

    if user.rol == "admin":
        objetivos_query = Objetivo.objects.all()
    else:
        if not mi_depto:
            messages.error(request, "No se pudo determinar el departamento.")
            return redirect("home")
        objetivos_query = Objetivo.objects.filter(departamento=mi_depto)

    objetivos_list = objetivos_query.prefetch_related(
        'objetivoempleado_set'
    ).order_by('-activo', '-fecha_creacion')

    for obj in objetivos_list:
        obj.esta_asignado = obj.objetivoempleado_set.exists()

    paginator = Paginator(objetivos_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    todos_departamentos = Departamento.objects.all()

    if user.rol == "admin":
        cargos_modal = Cargo.objects.all().distinct()
    else:
        cargos_modal = Cargo.objects.filter(cargodepartamento__departamento=mi_depto).distinct()

    context = {
        'objetivos': page_obj,
        'departamentos': todos_departamentos,
        'cargos': cargos_modal,
        'objetivo_a_asignar': request.GET.get("asignar"),
        'hoy': date.today(),
    }
    return render(request, 'objetivos.html', context)



@login_required
def obtener_datos_por_depto(request):
    depto_id = request.GET.get('depto_id')
    tipo = request.GET.get('tipo')  

    if not depto_id:
        return JsonResponse({'data': []})

    if tipo == 'empleado':
        empleados = Empleado.objects.filter(
            empleadocargo__cargo__cargodepartamento__departamento_id=depto_id,
            empleadocargo__fecha_fin__isnull=True
        ).distinct()
        data = [{'id': e.id, 'nombre': f"{e.nombre} {e.apellido}"} for e in empleados]

    elif tipo == 'cargo':
        cargos = Cargo.objects.filter(
            cargodepartamento__departamento_id=depto_id
        ).distinct()
        data = [{'id': c.id, 'nombre': c.nombre} for c in cargos]
    
    else:
        return JsonResponse({'error': 'Tipo no válido'}, status=400)

    return JsonResponse({'data': data})



@login_required
@require_POST
def crear_objetivo(request):
    id_objetivo = request.POST.get("id_objetivo")
    accion = request.POST.get("accion")
    
    datos = {
        'titulo': request.POST.get("titulo"),
        'descripcion': request.POST.get("descripcion"),
        'fecha_fin': request.POST.get("fecha_fin") or None,
        'es_recurrente': request.POST.get("es_recurrente") == "on",
    }

    if id_objetivo:
        objetivo = get_object_or_404(Objetivo, pk=id_objetivo)
        for key, value in datos.items():
            setattr(objetivo, key, value)
        objetivo.save()
        messages.success(request, "Objetivo actualizado.")
    else:
        empleado = Empleado.objects.get(pk=request.user.persona.pk)
        objetivo = Objetivo.objects.create(
            creado_por=request.user,
            departamento=empleado.departamento_actual(),
            fecha_creacion=date.today(),
            **datos
        )
        messages.success(request, "Objetivo creado.")

    if accion == "guardar_y_asignar":
        return redirect(f"{reverse('objetivos')}?asignar={objetivo.id}")
    return redirect("objetivos")



@login_required
@require_POST
def asignar_objetivo(request):
    objetivo_id = request.POST.get("objetivo_id")
    tipo = request.POST.get("tipo_asignacion")
    objetivo = get_object_or_404(Objetivo, id=objetivo_id)

    if tipo == "empleado":
        empleado_ids = request.POST.getlist("empleado_id")
        for emp_id in empleado_ids:
            ObjetivoEmpleado.objects.get_or_create(
                objetivo=objetivo,
                empleado_id=emp_id,
                fecha_asignacion=date.today(),
                defaults={
                    'completado': False,
                    'cargo': None, 
                    'fecha_limite': objetivo.fecha_fin
                }
            )
        messages.success(request, f"Objetivo asignado a {len(empleado_ids)} empleados.")
    
    elif tipo == "cargo":
        cargo_id = request.POST.get("cargo_id")
        cargo_obj = get_object_or_404(Cargo, id=cargo_id)
        empleados_del_cargo = Empleado.objects.filter(cargo=cargo_obj)
        
        for emp in empleados_del_cargo:
            ObjetivoEmpleado.objects.get_or_create(
                objetivo=objetivo,
                empleado=emp,
                fecha_asignacion=date.today(),
                defaults={
                    'cargo': cargo_obj, 
                    'completado': False,
                    'fecha_limite': objetivo.fecha_fin
                }
            )
        messages.success(request, f"Objetivo asignado a todos los empleados del cargo {cargo_obj.nombre}.")

    return redirect("objetivos")



@login_required
@require_POST
def activar_objetivo(request, id_objetivo):
    try:
        objetivo = get_object_or_404(Objetivo, id=id_objetivo)
        objetivo.activo = True 
        objetivo.save()
        messages.success(request, "Objetivo activado correctamente.")
    except Objetivo.DoesNotExist:
        messages.error(request, "El objetivo no existe.")
    return redirect('objetivos')



@login_required
@require_POST
def desactivar_objetivo(request, id_objetivo):
    try:
        objetivo = get_object_or_404(Objetivo, id=id_objetivo)
        objetivo.activo = False 
        objetivo.save()
        messages.success(request, "Objetivo desactivado correctamente.")
    except Objetivo.DoesNotExist:
        messages.error(request, "El objetivo no existe.")
    return redirect('objetivos')



@login_required
@require_POST
def eliminar_objetivo(request, id_objetivo):
    objetivo = get_object_or_404(Objetivo, id=id_objetivo)
    objetivo.delete()
    messages.success(request, "Objetivo eliminado y todas sus asignaciones borradas.")
    return redirect('objetivos')



@login_required
def obtener_asignaciones_objetivo(request):
    objetivo_id = request.GET.get('objetivo_id')
    objetivo = get_object_or_404(Objetivo, id=objetivo_id)
    
    empleados = list(objetivo.objetivoempleado_set.filter(cargo__isnull=True).values_list('empleado_id', flat=True))
    
    cargos = list(objetivo.objetivoempleado_set.filter(cargo__isnull=False).values_list('cargo_id', flat=True).distinct())

    return JsonResponse({'empleados': empleados, 'cargos': cargos})



@login_required
def marcar_objetivo(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        empleado = get_object_or_404(Empleado, persona__id=request.user.persona.id)
        objetivo_id = request.POST.get('objetivo_id')
        completado = request.POST.get('completado') == 'true'
        hoy = date.today()

        try:
            oe = ObjetivoEmpleado.objects.get(
                empleado=empleado,
                objetivo_id=objetivo_id,
                fecha_asignacion=hoy
            )
            oe.completado = completado
            oe.save()

            objetivos_hoy = ObjetivoEmpleado.objects.filter(
                empleado=empleado,
                fecha_asignacion=hoy
            )

            total = objetivos_hoy.count()
            hechos = objetivos_hoy.filter(completado=True).count()
            progreso = int((hechos / total) * 100) if total > 0 else 0

            return JsonResponse({'success': True, 'progreso': progreso})
        except ObjetivoEmpleado.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No se encontró la asignación para hoy.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'status': 405})
