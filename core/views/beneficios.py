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

