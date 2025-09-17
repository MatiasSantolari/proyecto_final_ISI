from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


@login_required
def logros(request):
    form = LogroForm()
    logrosList = Logro.objects.all().order_by('descripcion')

    paginator = Paginator(logrosList, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'logros.html', {
        'form': form,
        'logros': page_obj
    })


@login_required
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


@login_required
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