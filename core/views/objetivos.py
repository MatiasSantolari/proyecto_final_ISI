import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.utils.encoding import force_bytes
from datetime import date
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_POST
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from ..decorators import rol_requerido
from django.utils.timezone import now
from collections import defaultdict
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Min
from django.db.models import Q

def generar_objetivos_recurrentes(departamento):
    objetivos_recurrentes = Objetivo.objects.filter(
        departamento=departamento,
        activo=True,
        es_recurrente=True
    )

    for objetivo in objetivos_recurrentes:
        empleados_asignados = objetivo.objetivoempleado_set.values_list('empleado', flat=True).distinct()

        for emp_id in empleados_asignados:
            ObjetivoEmpleado.objects.get_or_create(
                objetivo=objetivo,
                empleado_id=emp_id,
                fecha_asignacion=date.today(),
                defaults={'completado': False}
            )


@login_required
def objetivos(request):
    user = request.user
    try:
        rol = Empleado.objects.get(pk=user.persona.id)
    except Empleado.DoesNotExist:
        messages.error(request, "No se encontró un empleado asociado a este usuario.")
        return redirect("home")

    departamento = rol.departamento_actual()

    if user.rol == "admin":
        objetivosList = Objetivo.objects.all().prefetch_related(
            Prefetch('objetivoempleado_set', queryset=ObjetivoEmpleado.objects.select_related('empleado')),
            Prefetch('objetivocargo_set', queryset=ObjetivoCargo.objects.select_related('cargo'))
        ).order_by('-activo', '-fecha_creacion').distinct()
    else:
        if departamento is None:
            messages.error(request, "No se pudo determinar el departamento del usuario.")
            return redirect("home")

        generar_objetivos_recurrentes(departamento)

        objetivosList = Objetivo.objects.filter(
            departamento=departamento
        ).prefetch_related(
            Prefetch('objetivoempleado_set', queryset=ObjetivoEmpleado.objects.select_related('empleado')),
            Prefetch('objetivocargo_set', queryset=ObjetivoCargo.objects.select_related('cargo'))
        ).order_by('-activo', '-fecha_creacion').distinct()



    objetivos_con_fechas = []
    for objetivo in objetivosList:
        tiene_empleados = objetivo.objetivoempleado_set.exists()
        tiene_cargos = objetivo.objetivocargo_set.exists()
        if tiene_empleados or tiene_cargos:
            objetivo.estado_asignacion = "Asignado"
        else:
            objetivo.estado_asignacion = "Sin Asignar"

        fecha_min_empleado = objetivo.objetivoempleado_set.aggregate(Min('fecha_asignacion'))['fecha_asignacion__min']
        fecha_min_cargo = objetivo.objetivocargo_set.aggregate(Min('fecha_asignacion'))['fecha_asignacion__min']
        fechas = [f for f in [fecha_min_empleado, fecha_min_cargo] if f is not None]
        objetivo.fecha_asignacion_representativa = min(fechas) if fechas else None

        objetivos_con_fechas.append(objetivo)

    # Ordenar por activo (descendente, True primero) y luego fecha_asignacion_representativa (descendente)
    objetivos_ordenados = objetivos_con_fechas

    empleados = Empleado.objects.filter(
        empleadocargo__cargo__cargodepartamento__departamento=departamento,
        empleadocargo__fecha_fin__isnull=True
    ).select_related('persona_ptr').distinct()

    cargos = Cargo.objects.filter(
        cargodepartamento__departamento=departamento
    ).distinct()

    form = ObjetivoForm()
    objetivo_a_asignar = request.GET.get("asignar")

    context = {
        'objetivos': objetivos_ordenados,
        'empleados': empleados,
        'cargos': cargos,
        'form': form,
        'objetivo_a_asignar': objetivo_a_asignar,
    }

    return render(request, 'objetivos.html', context)



@login_required
@require_POST
def crear_objetivo(request):
    accion = request.POST.get("accion")
    id_objetivo = request.POST.get("id_objetivo")
    titulo = request.POST.get("titulo")
    descripcion = request.POST.get("descripcion")
    fecha_fin = request.POST.get("fecha_fin")
    es_recurrente = request.POST.get("es_recurrente") == "on"

    try:
        empleado = Empleado.objects.get(pk=request.user.persona.pk)
        departamento = empleado.departamento_actual()
        if not departamento:
            messages.error(request, "No se pudo determinar el departamento actual.")
            return redirect("objetivos")
    except Empleado.DoesNotExist:
        messages.error(request, "No se encontró un empleado asociado al usuario.")
        return redirect("objetivos")

    if id_objetivo:
        try:
            objetivo = Objetivo.objects.get(pk=id_objetivo)
            objetivo.titulo = titulo
            objetivo.descripcion = descripcion
            objetivo.fecha_fin = fecha_fin or None
            objetivo.es_recurrente = es_recurrente
            objetivo.save()
            print(f"Objetivo editado: {objetivo} (id: {objetivo.id})")
        except Objetivo.DoesNotExist:
            messages.error(request, "No se encontró el objetivo a editar.")
            return redirect("objetivos")
    else:
        objetivo = Objetivo.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            fecha_creacion=date.today(),
            fecha_fin=fecha_fin or None,
            es_recurrente=es_recurrente,
            creado_por=request.user,
            departamento=departamento,
        )

    if accion == "guardar":
        messages.success(request, "Objetivo guardado correctamente.")
        return redirect("objetivos")

    if accion == "guardar_y_asignar":
        messages.success(request, "Objetivo guardado. Ahora asígnelo.")
        return redirect(f"{reverse('objetivos')}?asignar={objetivo.id}")



@login_required
@require_POST
def asignar_objetivo(request):
    objetivo_id = request.POST.get("objetivo_id")
    tipo = request.POST.get("tipo_asignacion")

    objetivo = get_object_or_404(Objetivo, id=objetivo_id)

    try:
        jefe = Empleado.objects.get(pk=request.user.persona.pk)
        departamento = jefe.departamento_actual()
    except Exception as e:
        messages.error(request, "No se pudo determinar el departamento del jefe.")
        return redirect("objetivos")

    if tipo == "empleado":
        empleado_ids = request.POST.getlist("empleado_id")
        empleados = Empleado.objects.filter(id__in=empleado_ids)

        for emp in empleados:
            obj_emp, created = ObjetivoEmpleado.objects.get_or_create(
                objetivo=objetivo,
                empleado=emp,
                defaults={
                    'completado': False,
                    "fecha_asignacion": date.today(),
                }
            )
            if not created:
                obj_emp.fecha_asignacion = date.today()
                obj_emp.save()

        messages.success(request, "Objetivo asignado a empleados correctamente.")

    elif tipo == "cargo":
        cargo_id = request.POST.get("cargo_id")
        cargo = get_object_or_404(Cargo, id=cargo_id)

        oc, created = ObjetivoCargo.objects.get_or_create(
            objetivo=objetivo,
            cargo=cargo,
            defaults={
                'completado': False,
                "fecha_asignacion": date.today()
            }
        )
        if not created:
            oc.activo = True
            oc.fecha_asignacion = date.today()
            oc.save()


        messages.success(request, "Objetivo asignado a todos los empleados del cargo.")

    else:
        messages.error(request, "Debe seleccionar un tipo de asignación válida.")

    return redirect("objetivos")



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
    try:
        objetivo = get_object_or_404(Objetivo, id=id_objetivo)
        objetivo.delete()
        messages.success(request, "Objetivo eliminado correctamente.")
    except Objetivo.DoesNotExist:
        messages.error(request, "El objetivo no existe.")
    return redirect('objetivos')


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

#

@login_required
def obtener_asignaciones_objetivo(request):
    objetivo_id = request.GET.get('objetivo_id')
    if not objetivo_id:
        return JsonResponse({'error': 'Falta el ID del objetivo'}, status=400)

    objetivo = get_object_or_404(Objetivo, id=objetivo_id)

    empleados_asignados = list(objetivo.objetivoempleado_set.values_list('empleado_id', flat=True))
    cargos_asignados = list(objetivo.objetivocargo_set.values_list('cargo_id', flat=True))

    return JsonResponse({
        'empleados': empleados_asignados,
        'cargos': cargos_asignados
    })

#

@login_required
def obtener_datos_asignacion(request):
    tipo = request.GET.get('tipo')
    usuario = request.user

    try:
        empleado = Empleado.objects.get(persona=usuario.persona)
        departamento = empleado.departamento_actual()
    except:
        return JsonResponse({'error': 'No se pudo determinar el departamento del usuario'}, status=400)

    if tipo == 'empleado':
        empleados = Empleado.objects.filter(
            empleadocargo__cargo__cargodepartamento__departamento=departamento,
            empleadocargo__activo=True
        ).distinct()
        data = [{'id': emp.id, 'nombre': str(emp.persona)} for emp in empleados]
    elif tipo == 'cargo':
        cargos = Cargo.objects.filter(
            cargodepartamento__departamento=departamento
        ).distinct()
        data = [{'id': cargo.id, 'nombre': cargo.nombre} for cargo in cargos]
    else:
        return JsonResponse({'error': 'Tipo no válido'}, status=400)

    return JsonResponse({'data': data})


@login_required
def marcar_objetivo(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user = request.user
        persona = getattr(user, 'persona', None)
        if not persona or not hasattr(persona, 'empleado'):
            return JsonResponse({'success': False, 'error': 'Empleado no encontrado.'})

        empleado = persona.empleado
        objetivo_id = request.POST.get('objetivo_id')
        completado = request.POST.get('completado') == 'true'
        hoy = date.today()

        try:
            oe, created = ObjetivoEmpleado.objects.get_or_create(
                empleado=empleado,
                objetivo_id=objetivo_id,
                defaults={'completado': completado}
            )
            if not created:
                oe.completado = completado
                oe.save()

            no_recurrentes = ObjetivoEmpleado.objects.filter(
                empleado=empleado,
                objetivo__activo=True,
                objetivo__es_recurrente=False
            ).filter(
                Q(objetivo__fecha_fin__isnull=True) | Q(objetivo__fecha_fin__gte=hoy)
            )

            recurrentes = ObjetivoEmpleado.objects.filter(
                empleado=empleado,
                objetivo__activo=True,
                objetivo__es_recurrente=True,
                fecha_asignacion=hoy
            )

            objetivos_hoy = (no_recurrentes | recurrentes).distinct()

            total_objetivos = objetivos_hoy.count()
            completados = objetivos_hoy.filter(completado=True).count()
            progreso = int((completados / total_objetivos) * 100) if total_objetivos > 0 else 0

            return JsonResponse({'success': True, 'progreso': progreso})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})