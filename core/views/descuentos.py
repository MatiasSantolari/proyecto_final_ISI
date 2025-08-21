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
