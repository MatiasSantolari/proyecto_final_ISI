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

def logros(request):
    form = LogroForm()
    logrosList = Logro.objects.all()
    return render(request, 'logros.html', {
        'form': form,
        'logros': logrosList
    })

def crear_logro(request):
    id_logro = request.POST.get('id_logro')

    if request.method == 'POST':
        if id_logro:
            logro = get_object_or_404(Logro, pk=id_logro)
            form = LogroForm(request.POST, instance=logro)
        else:
            form = LogroForm(request.POST)

        if form.is_valid():
            form.save()
            if id_logro:
                messages.success(request, "El logro se actualizó correctamente.")
            else:
                messages.success(request, "El logro se creó correctamente.")
            return redirect('logros')
        else:
            messages.error(request, "Hubo un error al guardar el logro. Verifique los datos ingresados.")

    else:
        form = LogroForm()

    logrosList = Logro.objects.all()
    return render(request, 'logros.html', {'form': form, 'logros': logrosList})


@require_POST
def eliminar_logro(request, id_logro):
    try:
        logro = get_object_or_404(Logro, id=id_logro)
        LogroEmpleado.objects.filter(logro=logro).delete() # Elimina todas las relaciones de empleados con este logro
        logro.delete()
        messages.success(request, "logro eliminado correctamente.")
    except Logro.DoesNotExist:
        messages.error(request, "El logro no existe.")
    return redirect('logros')