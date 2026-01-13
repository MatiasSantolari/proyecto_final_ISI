from django.shortcuts import render
from ..models import *
from ..forms import *
from personas.forms import PersonaForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import date
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import requests
import os
from django.core.files.base import ContentFile
from django.urls import reverse
from django.contrib.auth import logout


@login_required
@require_POST
def cambiar_vista(request):
    if not request.user.is_authenticated:
        logout(request)
        messages.error(request, "Tu sesión ha expirado. Por favor, inicia sesión de nuevo.")
        return redirect(reverse('home'))
    
    rol = request.POST.get('rol')
    if rol in ['admin', 'empleado', 'jefe', 'gerente']:
        request.session['rol_actual'] = rol
        messages.success(request, f"Vista cambiada a {rol.capitalize()}.")
        return redirect('home')
    else:
        messages.error(request, "Rol seleccionado no válido.")
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
    if not request.user.persona:
        return redirect('create_profile')
    
    user = request.user
    rol_actual = request.session.get('rol_actual', user.rol)

    departamentos_disponibles = Departamento.objects.all().order_by('nombre')

    context = {
        'rol_actual': rol_actual, 
        'usuario': user,
        'departamentos_disponibles': departamentos_disponibles,
        }

    empleado = None
    
    if rol_actual == 'empleado':
        persona = user.persona

        if hasattr(persona, 'empleado'):
            empleado = persona.empleado
            crear_objetivos_recurrentes_hoy(empleado)
            hoy = date.today()
           
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

            oe_queryset = no_recurrentes | recurrentes
            oe_queryset = oe_queryset.select_related('objetivo').distinct()

            objetivos_con_estado = [{'objetivo': oe.objetivo, 'completado': oe.completado} for oe in oe_queryset]

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

    departamentos = Departamento.objects.all()
    context['departamentos'] = departamentos

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
def create_persona(request):
    social = request.user.social_auth.filter(provider='google-oauth2').first()

    initial_data = {}
    avatar_url = None

    if social:
        initial_data = {
            'nombre': (social.extra_data.get('nombre') or '').capitalize(),
            'apellido': (social.extra_data.get('apellido') or '').capitalize(),
            'email': social.extra_data.get('email'),
        }
        avatar_url = social.extra_data.get('picture')
    
#    print("INITIAL DATA:", initial_data)
#    print("AVATAR URL:", avatar_url)

    if request.method == 'POST':
        form = PersonaForm(
            request.POST,
            request.FILES,
            include_admin_fields=False,
            initial=initial_data,
        )
        if form.is_valid():
            persona = form.save(commit=False)
            if avatar_url and not persona.avatar:
                try:
                    response_img = requests.get(avatar_url, stream=True)
                    if response_img.status_code == 200:
                        fname = os.path.basename(avatar_url)
                        if 'googleusercontent' in fname:
                             fname = f"avatar_{request.user.username}.jpg"
                             
                        persona.avatar.save(
                            fname, 
                            ContentFile(response_img.content), 
                            save=False
                        )

                except requests.exceptions.RequestException as e:
                    print(f"ERROR al descargar avatar de Google: {e}")
            
            persona.save()

            request.user.persona = persona
            request.user.save()
            return redirect('home')
    else:
        form = PersonaForm(
            include_admin_fields=False,
            initial=initial_data
        )

    return render(
        request, 
        'auth/create_profile.html', 
        {
            'form': form,
            'avatar_url': avatar_url,
        }
    )




@login_required
def perfil_usuario(request):
    persona = request.user.persona

    form = PersonaForm(
        request.POST or None,
        request.FILES or None,
        include_admin_fields=False,
        instance=persona
    )

    if request.method == 'POST':
        if form.is_valid():
            eliminar_cv = request.POST.get('eliminar_cvitae') == '1'
            nuevo_cv = request.FILES.get('cvitae')

            if eliminar_cv and persona.cvitae:
                if persona.cvitae.storage.exists(persona.cvitae.name):
                    persona.cvitae.delete(save=False)
                persona.cvitae = None

            if nuevo_cv:
                persona.cvitae = nuevo_cv

            persona.save()
            return redirect('user_perfil')


    cargo_actual = None
    departamento_actual = None
    empleado = getattr(persona, 'empleado', None)
    if empleado:
        cargo_actual = empleado.cargo_actual_nombre()
        departamento_actual = empleado.departamento_actual_nombre()

    dias_cumple = None
    if persona.fecha_nacimiento:
        hoy = date.today()
        cumple = persona.fecha_nacimiento
        siguiente_cumple = cumple.replace(year=hoy.year)
        if siguiente_cumple < hoy:
            siguiente_cumple = siguiente_cumple.replace(year=hoy.year + 1)
        dias_cumple = (siguiente_cumple - hoy).days

    context = {
        'form': form,
        'cargo_actual': cargo_actual,
        'departamento_actual': departamento_actual,
        'dias_cumple': dias_cumple,
    }

    return render(request, 'user_perfil.html', context)
