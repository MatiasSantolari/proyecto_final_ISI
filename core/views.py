import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from .models import *
from .forms import *
from personas.forms import PersonaForm
from django.core.mail import send_mail
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
from django.db.models import Min
from django.db.models import Q

"""
@login_required
@rol_requerido('admin', 'gerente')
def dashboard_admin(request):
    return render(request, 'core/dashboard_admin.html')

@login_required
@rol_requerido('empleado')
def dashboard_empleado(request):
    return render(request, 'core/dashboard_empleado.html')

@login_required
def dashboard_normal(request):
    return render(request, 'core/dashboard_normal.html')
"""



@login_required
@require_POST
def cambiar_vista(request):
    if request.method == 'POST':
        rol = request.POST.get('rol')
        if rol in ['admin', 'empleado', 'jefe', 'gerente']:
            request.session['rol_actual'] = rol
            messages.success(request, f"Vista cambiada a {rol.capitalize()}.")
    return redirect('home')


#
def crear_objetivos_recurrentes_hoy(empleado):
    hoy = date.today()
    recurrentes = Objetivo.objects.filter(es_recurrente=True, activo=True)
    for obj in recurrentes:
        ObjetivoEmpleado.objects.get_or_create(
            objetivo=obj,
            empleado=empleado,
            fecha_asignacion=hoy,
            defaults={'completado': False}
        )

@login_required
def home(request):
    user = request.user
    rol_actual = request.session.get('rol_actual', user.rol)

    context = {'rol_actual': rol_actual, 'usuario': user}

    if not hasattr(user, 'persona'):
        return redirect('create_profile')

    empleado = None
    
    if rol_actual == 'empleado':
        persona = user.persona

        if hasattr(persona, 'empleado'):
            empleado = persona.empleado
            crear_objetivos_recurrentes_hoy(empleado)
            hoy = date.today()
           
            # Objetivos no recurrentes: vigentes
            no_recurrentes = ObjetivoEmpleado.objects.filter(
                empleado=empleado,
                objetivo__activo=True,
                objetivo__es_recurrente=False
            ).filter(
                Q(objetivo__fecha_fin__isnull=True) | Q(objetivo__fecha_fin__gte=hoy)
            )

            
            # Objetivos recurrentes: asignados hoy
            recurrentes = ObjetivoEmpleado.objects.filter(
                empleado=empleado,
                objetivo__activo=True,
                objetivo__es_recurrente=True,
                fecha_asignacion=hoy
            )

            # Todos los objetivos a mostrar
            oe_queryset = no_recurrentes | recurrentes
            oe_queryset = oe_queryset.select_related('objetivo').distinct()

            objetivos_con_estado = [{'objetivo': oe.objetivo, 'completado': oe.completado} for oe in oe_queryset]

            # Calcular progreso solo con objetivos vigentes y pendientes
            oe_para_progreso = []
            for oe in oe_queryset:
                if oe.objetivo.es_recurrente and oe.fecha_asignacion == hoy:
                    oe_para_progreso.append(oe)
                elif not oe.objetivo.es_recurrente and (oe.objetivo.fecha_fin is None or oe.objetivo.fecha_fin >= hoy):
                    oe_para_progreso.append(oe)

            
            total = len(objetivos_con_estado)
            completados = sum(1 for o in objetivos_con_estado if o['completado'])
            progreso = int((completados / total) * 100) if total > 0 else 0

            context.update({
                'objetivos_con_estado': objetivos_con_estado,
                'progreso': progreso,
                'empleado': empleado,
            })

        if empleado is None:
            context.update({
                'objetivos_con_estado': [],
                'progreso': 0,
                'empleado': None,
            })

    return render(request, 'index.html', context)
#


def registrar_usuario(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cuenta creada correctamente. Iniciá sesión.")
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'auth/register.html', {'form': form})


@login_required
@require_POST
def create_persona(request):
    if request.method == 'POST':
        form = PersonaForm(request.POST, request.FILES, include_admin_fields=False)
        if form.is_valid():
            persona = form.save(commit=False)

            persona.save()

            user = request.user
            user.persona = persona
            user.save()

            return redirect('home')
    else:
        form = PersonaForm(include_admin_fields=False)

    return render(request, 'auth/create_profile.html', {'form': form})


@login_required
def perfil_usuario(request):
    persona = request.user.persona

    form = PersonaForm(
        request.POST or None,
        request.FILES or None,
        include_admin_fields=False,
        instance=persona,
        initial={
            'fecha_nacimiento': persona.fecha_nacimiento.strftime('%Y-%m-%d') if persona.fecha_nacimiento else ''
        }
    )

    if request.method == 'POST' and form.is_valid():
        # Si el usuario solicitó eliminar el CV
        if request.POST.get('eliminar_cvitae') == '1':
            if persona.cvitae:
                if persona.cvitae.storage.exists(persona.cvitae.name):
                    persona.cvitae.delete(save=False)
                persona.cvitae = None

        form.save()
        return redirect('user_perfil')

    return render(request, 'user_perfil.html', {'form': form})


##########################

########## CRUD CARGO #################

@login_required
def cargos(request):
    cargos_con_sueldo = []

    relaciones = CargoDepartamento.objects.select_related('cargo', 'departamento')

    for relacion in relaciones:
        cargo = relacion.cargo
        departamento = relacion.departamento

        # Sueldo base (último)
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

    form = CargoForm()
    return render(request, 'cargos.html', {'cargos': cargos_con_sueldo, 'form': form})



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


################

######CRUD Departamentos #####################
@login_required
def departamentos(request):
    form = DepartamentoForm()
    departamentosList = Departamento.objects.all()
    return render(request, 'departamentos.html', {
        'form': form,
        'departamentos': departamentosList
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

            return redirect('departamentos')

    else:
        form = DepartamentoForm()

    departamentosList = Departamento.objects.all()
    return render(request, 'departamentos.html', {'form': form, 'departamentos': departamentosList})


@login_required
@require_POST
def eliminar_departamento(request, id_departamento):
    departamento = get_object_or_404(Departamento, id=id_departamento)
    relaciones = CargoDepartamento.objects.filter(departamento=departamento)

    for relacion in relaciones:
        cargo = relacion.cargo
        relacion.delete()
        otros = CargoDepartamento.objects.filter(cargo=cargo).exists()
        if not otros:
            cargo.delete()

    departamento.delete()

    return redirect('departamentos')


###################################
##########  POSTULARSE  ###########
@login_required
def listar_ofertas(request):
    persona = request.user.persona  
    cargos_departamento = CargoDepartamento.objects.select_related('cargo', 'departamento')\
        .filter(visible=True)\
        .exclude(cargo__nombre="ADMIN")\
        .exclude(departamento__nombre="ADMIN")

    solicitudes = Solicitud.objects.filter(persona=persona)
    postulaciones = {s.cargo.id: s.fecha for s in solicitudes}

    nombre_cv = os.path.basename(persona.cvitae.name) if persona.cvitae else None
        
    context = {
        'cargos_departamento': cargos_departamento,
        'postulaciones': postulaciones,
        'nombre_cv': nombre_cv,
    }
    return render(request, 'ofertas_empleo.html', context)



@login_required
def postularse_a_cargo(request, cargo_id):
    if request.method == 'POST':
        persona = request.user.persona
        cargo = get_object_or_404(Cargo, pk=cargo_id)

        solicitud = Solicitud.objects.filter(persona=persona, cargo=cargo).order_by('-fecha').first()
        if solicitud:
            dias_espera = 30
            if (now().date() - solicitud.fecha).days < dias_espera:
                return JsonResponse({'exito': False, 'mensaje': 'Ya te postulaste recientemente a este cargo.'})

        forzar = request.POST.get('forzar_sin_cv', 'false') == 'true'
        if not persona.cvitae and not forzar:
            return JsonResponse({'requiere_confirmacion_cv': True})

        es_interno = request.user.rol in ['empleado', 'jefe', 'gerente', 'admin']
        Solicitud.objects.create(
            persona=persona,
            cargo=cargo,
            estado='pendiente',
            es_interno=es_interno,
        )
        return JsonResponse({'exito': True})



@login_required
def actualizar_cv_ajax(request):
    if request.method == 'POST':
        persona = request.user.persona
        archivo_cv = request.FILES.get('cv')

        if archivo_cv:
            if persona.cvitae:
                ruta_anterior = persona.cvitae.path
                if os.path.isfile(ruta_anterior):
                    os.remove(ruta_anterior)

            persona.cvitae = archivo_cv
            persona.save()
            return JsonResponse({'exito': True})

        return JsonResponse({'exito': False, 'error': 'No se envió ningún archivo.'})
    return JsonResponse({'exito': False, 'error': 'Método no permitido.'})


@login_required
@staff_member_required
def ver_postulaciones_admin(request):
    solicitud_visible = Prefetch(
        'cargo__solicitud_set',
        queryset=Solicitud.objects.filter(visible=True).select_related('persona').order_by('-fecha'),
        to_attr='solicitudes_visibles'
    )

    todas_solicitudes = Prefetch(
        'cargo__solicitud_set',
        queryset=Solicitud.objects.select_related('persona').order_by('-fecha'),
        to_attr='solicitudes'
    )

    visibles = CargoDepartamento.objects.select_related('cargo', 'departamento') \
        .filter(visible=True) \
        .exclude(cargo__nombre="ADMIN")\
        .exclude(departamento__nombre="ADMIN")\
        .prefetch_related(solicitud_visible)

    no_visibles = CargoDepartamento.objects.select_related('cargo', 'departamento') \
        .filter(visible=False) \
        .exclude(cargo__nombre="ADMIN")\
        .exclude(departamento__nombre="ADMIN")\
        .prefetch_related(solicitud_visible)

    todas = CargoDepartamento.objects.select_related('cargo', 'departamento') \
        .exclude(cargo__nombre="ADMIN")\
        .exclude(departamento__nombre="ADMIN")\
        .prefetch_related(todas_solicitudes)


    cargos_visibles_por_dpto = defaultdict(list)
    for relacion in visibles:
        cargos_visibles_por_dpto[relacion.departamento.nombre].append(relacion)

    cargos_no_visibles_por_dpto = defaultdict(list)
    for relacion in no_visibles:
        cargos_no_visibles_por_dpto[relacion.departamento.nombre].append(relacion)

    todas_por_dpto = defaultdict(list)
    for relacion in todas:
        todas_por_dpto[relacion.departamento.nombre].append(relacion)

    context = {
        'cargos_visibles_por_dpto': dict(cargos_visibles_por_dpto),
        'cargos_no_visibles_por_dpto': dict(cargos_no_visibles_por_dpto),
        'todas': dict(todas_por_dpto),
    }

    return render(request, 'admin_postulaciones.html', context)


@login_required
@require_POST
@staff_member_required
def cambiar_estado_solicitud(request):
    solicitud_id = request.POST.get('solicitud_id')
    nuevo_estado = request.POST.get('nuevo_estado')

    if nuevo_estado not in ['pendiente', 'seleccionado', 'descartado']:
        return JsonResponse({'exito': False, 'mensaje': 'Estado inválido'})

    try:
        solicitud = Solicitud.objects.get(id=solicitud_id)
        solicitud.estado = nuevo_estado
        solicitud.save()
        return JsonResponse({'exito': True})
    except Solicitud.DoesNotExist:
        return JsonResponse({'exito': False, 'mensaje': 'Solicitud no encontrada'})


@login_required
@require_POST
@staff_member_required
def finalizar_postulaciones_cargo(request):
    cargo_id = request.POST.get('cargo_id')
    
    ##Solicitud.objects.filter(cargo_id=cargo_id, visible=True).update(visible=False)
    CargoDepartamento.objects.filter(cargo_id=cargo_id).update(visible=False)

    return JsonResponse({'exito': True})


@login_required
@require_POST
@staff_member_required
def limpiar_postulantes_cargo(request):
    cargo_id = request.POST.get('cargo_id')
    Solicitud.objects.filter(cargo_id=cargo_id, visible=True).update(visible=False)
    return JsonResponse({'exito': True})


@login_required
@require_POST
@staff_member_required
def habilitar_cargo_para_postulaciones(request):
    cargo_id = request.POST.get('cargo_id')
    CargoDepartamento.objects.filter(cargo_id=cargo_id).update(visible=True)
    return JsonResponse({'exito': True})


############### CRUD OBJETIVOS ##################
###############                ##################

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



################ CRUD Beneficios #####################

@login_required
def beneficios(request):
    form = BeneficioForm()
    beneficiosList = Beneficio.objects.all()

    for b in beneficiosList:
        if b.descripcion:
            b.descripcion = b.descripcion.capitalize()

    return render(request, 'beneficios.html', {
        'form': form,
        'beneficios': beneficiosList
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
            return redirect('beneficios')

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



################ CRUD Descuentos #####################

@login_required
def descuentos(request):
    form = DescuentoForm()
    descuentosList = Descuento.objects.all()

    for b in descuentosList:
        if b.descripcion:
            b.descripcion = b.descripcion.capitalize()

    return render(request, 'descuentos.html', {
        'form': form,
        'descuentos': descuentosList
    })


@login_required
@require_POST
def crear_descuento(request):
    id_descuento = request.POST.get('id_descuento')

    if request.method == 'POST':
        if id_descuento:
            descuento = get_object_or_404(Descuento, pk=id_descuento)
            form = DescuentoForm(request.POST, instance=descuento)
        else:
            form = DescuentoForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('descuentos')

    else:
        form = DescuentoForm()

    descuentosList = Descuento.objects.all()
    return render(request, 'descuentos.html', {
        'form': form,
        'descuentos': descuentosList
    })


@login_required
@require_POST
def activar_descuento(request, id_descuento):
    try:
        descuento = get_object_or_404(Descuento, id=id_descuento)
        descuento.activo = True
        descuento.save()
        messages.success(request, "descuento activado correctamente.")
    except Descuento.DoesNotExist:
        messages.error(request, "El descuento no existe.")
    return redirect('descuentos')


@login_required
@require_POST
def desactivar_descuento(request, id_descuento):
    try:
        descuento = get_object_or_404(Descuento, id=id_descuento)
        descuento.activo = False
        descuento.save()
        messages.success(request, "descuento desactivado correctamente.")
    except Descuento.DoesNotExist:
        messages.error(request, "El descuento no existe.")
    return redirect('descuentos')


@login_required
@require_POST
def eliminar_descuento(request, id_descuento):
    try:
        descuento = get_object_or_404(Descuento, id=id_descuento)
        descuento.delete()
        messages.success(request, "descuento eliminado correctamente.")
    except Descuento.DoesNotExist:
        messages.error(request, "El descuento no existe.")
    return redirect('descuentos')


##################################################


def agregar_sueldo_base(request): return render(request, 'agregar_sueldo_base.html')
def calcular_bonificaciones(request): return render(request, 'calcular_bonificaciones.html')
def capacitaciones(request): return render(request, 'capacitaciones.html')
def competencias(request): return render(request, 'competencias.html')
#def contratos(request): return render(request, 'contratos.html')
def costos_de_personal(request): return render(request, 'costos_de_personal.html')
def criterios_evaluacion(request): return render(request, 'criterios_evaluacion.html')
def empleados(request): return render(request, 'empleados.html')
def evaluacion_desempeno(request): return render(request, 'evaluacion_desempeno.html')
def habilidades(request): return render(request, 'habilidades.html')
def instituciones(request): return render(request, 'instituciones.html')
#def logros(request): return render(request, 'logros.html')
def nominas(request): return render(request, 'nominas.html')

def postulantes(request): return render(request, 'postulantes.html')
def publicar_ofertas_de_empleo(request): return render(request, 'publicar_ofertas_de_empleo.html')
#def registrar_asistencia(request): return render(request, 'registrar_asistencia.html')
def solicitudes_nuevos_empleados(request): return render(request, 'solicitudes_nuevos_empleados.html')
def tipo_criterio_evaluacion(request): return render(request, 'tipo_criterio_evaluacion.html')
#def tipos_contrato(request): return render(request, 'tipos_contrato.html')
def competencias_faltantes(request): return render(request, 'competencias_faltantes.html')
def costos_de_contratacion(request): return render(request, 'costos_de_contratacion.html')
def reporte_evaluacion_desempeno(request): return render(request, 'reporte_evaluacion_desempeno.html')
def contratar_nuevo_empleado(request): return render(request, 'contratar_nuevo_empleado.html')
def ausencias_retardos(request): return render(request, 'ausencias_retardos.html')
