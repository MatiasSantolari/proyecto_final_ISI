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
def nominas(request):
    departamento = request.GET.get('departamento', '')
    mes = request.GET.get('mes', '')
    anio = request.GET.get('anio', '')

    nominas_list = (
        Nomina.objects
        .select_related('empleado')
        .prefetch_related(
            'empleado__empleadocargo_set__cargo__cargodepartamento_set__departamento'
        )
        .all()
    )

    if departamento:
        nominas_list = nominas_list.filter(
            empleado__empleadocargo__cargo__cargodepartamento__departamento__nombre=departamento
        )

    if mes and anio:
        nominas_list = nominas_list.filter(
            fecha_generacion__month=int(mes),
            fecha_generacion__year=int(anio)
        )

    nominas_list = nominas_list.order_by('-fecha_generacion')

    return render(request, 'nominas.html', {
        'nominas': nominas_list,
    })

'''
@login_required
@require_POST
def editar_nomina(request):
    id_nomina = request.POST.get('id_nomina')

    if request.method == 'POST':
        if id_nomina:
            nomina = get_object_or_404(Nomina, pk=id_nomina)
            form = NominaForm(request.POST, instance=nomina)
        else:
            form = NominaForm(request.POST)

        if form.is_valid():
            nueva_nomina = form.save()
            return redirect('nominas')

    else:
        form = NominaForm()

    nominasList = Nomina.objects.all()
    return render(request, 'nominas.html', {'form': form, 'nominas': nominasList})
'''


@login_required
@require_POST
def cambiar_estado_nomina(request, id_nomina):
    nomina = get_object_or_404(Nomina, pk=id_nomina)
    if nomina.estado == 'vigente':
        nomina.estado = 'anulada'
        messages.success(request, "La nómina fue anulada correctamente.")
    else:
        nomina.estado = 'vigente'
        messages.success(request, "La nómina fue restaurada correctamente.")
    nomina.save()
    return redirect('nominas')
