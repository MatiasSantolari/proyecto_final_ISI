import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
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
        form = PersonaFormCreate(request.POST, request.FILES)
        if form.is_valid():
            persona = form.save(commit=False)

            persona.save()

            user = request.user
            user.persona = persona
            user.save()

            return redirect('home')
    else:
        form = PersonaFormCreate()

    return render(request, 'auth/create_profile.html', {'form': form})


@login_required
def perfil_usuario(request):
    persona = request.user.persona

    form = PersonaFormCreate(
        request.POST or None,
        request.FILES or None,
        instance=persona,
        initial={
            'fecha_nacimiento': persona.fecha_nacimiento.strftime('%Y-%m-%d') if persona.fecha_nacimiento else ''
        }
    )

    if request.method == 'POST' and form.is_valid():
        # Si el usuario solicito eliminar el CV
        if request.POST.get('eliminar_cvitae') == '1':
            if persona.cvitae:
                if persona.cvitae.storage.exists(persona.cvitae.name):
                    persona.cvitae.delete(save=False)
                persona.cvitae = None

        form.save()
        return redirect('user_perfil')

    return render(request, 'user_perfil.html', {'form': form})
