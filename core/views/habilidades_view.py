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

def habilidades(request):
    form = HabilidadForm()
    habilidadesList = Habilidad.objects.all()
    return render(request, 'habilidades.html', {
        'form': form,
        'habilidades': habilidadesList
    })

def crear_habilidad(request):
    id_habilidad = request.POST.get('id_habilidad')

    if request.method == 'POST':
        if id_habilidad:
            habilidad = get_object_or_404(Habilidad, pk=id_habilidad)
            form = HabilidadForm(request.POST, instance=habilidad)
        else:
            form = HabilidadForm(request.POST)

        if form.is_valid():
            nueva_habilidad = form.save()
            return redirect('habilidades')

    else:
        form = HabilidadForm()

    habilidadesList = Habilidad.objects.all()
    return render(request, 'habilidades.html', {'form': form, 'habilidades': habilidadesList})

@require_POST
def eliminar_habilidad(request, id_habilidad):
    habilidad = get_object_or_404(Habilidad, id=id_habilidad)
    HabilidadEmpleado.objects.filter(habilidad=habilidad).delete() # Elimina todas las relaciones de empleados con esta habilidad
    habilidad.delete()
    return redirect('habilidades')