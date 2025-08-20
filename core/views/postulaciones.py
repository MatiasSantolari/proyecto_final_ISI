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
from django.http import HttpResponse, JsonResponse
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

def listar_ofertas(request):
    persona = request.user.persona
    cargos_departamento = CargoDepartamento.objects.select_related('cargo', 'departamento') \
        .filter(visible=True)  # Mostramos todos los cargos visibles, sin importar vacantes

    solicitudes = Solicitud.objects.filter(persona=persona)
    postulaciones = {s.cargo.id: s.fecha for s in solicitudes}

    nombre_cv = os.path.basename(persona.cvitae.name) if persona.cvitae else None

    context = {
        'cargos_departamento': cargos_departamento,
        'postulaciones': postulaciones,
        'nombre_cv': nombre_cv,
    }
    return render(request, 'ofertas_empleo.html', context)


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
            # Eliminar archivo anterior si existe
            if persona.cvitae:
                ruta_anterior = persona.cvitae.path
                if os.path.isfile(ruta_anterior):
                    os.remove(ruta_anterior)

            persona.cvitae = archivo_cv
            persona.save()
            return JsonResponse({'exito': True})

        return JsonResponse({'exito': False, 'error': 'No se envió ningún archivo.'})
    return JsonResponse({'exito': False, 'error': 'Método no permitido.'})


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
        .prefetch_related(solicitud_visible)

    no_visibles = CargoDepartamento.objects.select_related('cargo', 'departamento') \
        .filter(visible=False) \
        .prefetch_related(solicitud_visible)

    todas = CargoDepartamento.objects.select_related('cargo', 'departamento') \
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


@require_POST
@staff_member_required
def finalizar_postulaciones_cargo(request):
    cargo_id = request.POST.get('cargo_id')

    ##Solicitud.objects.filter(cargo_id=cargo_id, visible=True).update(visible=False)
    CargoDepartamento.objects.filter(cargo_id=cargo_id).update(visible=False)

    return JsonResponse({'exito': True})


@require_POST
@staff_member_required
def limpiar_postulantes_cargo(request):
    cargo_id = request.POST.get('cargo_id')
    Solicitud.objects.filter(cargo_id=cargo_id, visible=True).update(visible=False)
    return JsonResponse({'exito': True})


@require_POST
@staff_member_required
def habilitar_cargo_para_postulaciones(request):
    cargo_id = request.POST.get('cargo_id')
    CargoDepartamento.objects.filter(cargo_id=cargo_id).update(visible=True)
    return JsonResponse({'exito': True})
