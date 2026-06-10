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
from django.db import models
from django.db import transaction


@login_required
def logros(request):
    form = LogroForm()
    formB = BeneficioForm()
    
    orden_activos = Case(
        When(activo=False, then=2),
        default=1,
        output_field=IntegerField(),
    )

    logrosList = (
        Logro.objects.all()
        .annotate(
            prioridad_activo=orden_activos, 
            beneficio_asociado=models.Subquery(
                LogroBeneficio.objects.filter(logro_id=models.OuterRef('pk')).values('beneficio__descripcion')[:1]
            ),
            beneficio_id_asociado=models.Subquery(
                LogroBeneficio.objects.filter(logro_id=models.OuterRef('pk')).values('beneficio_id')[:1]
            ),
            beneficio_monto=models.Subquery(
                LogroBeneficio.objects.filter(logro_id=models.OuterRef('pk')).values('beneficio__monto')[:1]
            ),
            beneficio_porcentaje=models.Subquery(
                LogroBeneficio.objects.filter(logro_id=models.OuterRef('pk')).values('beneficio__porcentaje')[:1]
            )
        )
        .order_by('prioridad_activo', 'descripcion')
    )

    paginator = Paginator(logrosList, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'logros.html', {
        'form': form,
        'formB': formB,
        'logros': page_obj
    })



@login_required
def crear_logro(request):
    id_logro = request.POST.get('id_logro')

    if request.method == 'POST':
        if id_logro:
            logro = get_object_or_404(Logro, pk=id_logro)
            try:    
                logro_beneficio_rel = LogroBeneficio.objects.get(logro=logro)
                form = LogroForm(request.POST, initial={'beneficio': logro_beneficio_rel.beneficio_id}, instance=logro)
            except LogroBeneficio.DoesNotExist:
                 form = LogroForm(request.POST, instance=logro)
        else:
            form = LogroForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                logro = form.save()
                beneficio_seleccionado = form.cleaned_data.get('beneficio')
                
                LogroBeneficio.objects.filter(logro=logro).delete()

                if beneficio_seleccionado:
                    LogroBeneficio.objects.create(logro=logro, beneficio=beneficio_seleccionado)
                
                if id_logro:
                    messages.success(request, "El logro se actualizó correctamente.")
                else:
                    messages.success(request, "El logro se creó correctamente.")
                return redirect('logros')
        else:
            messages.error(request, "Hubo un error al guardar el logro. Verifique los datos ingresados.")

    return redirect('logros')



@login_required
@require_POST
def eliminar_logro(request, id_logro):
    logro = get_object_or_404(Logro, id=id_logro)
    logro.activo = False
    logro.save()
    
    messages.success(request, f"El logro '{logro.descripcion}' ha sido desactivado correctamente.")
    return redirect('logros')


@login_required
@require_POST
def reactivar_logro(request, id_logro):
    logro = get_object_or_404(Logro, id=id_logro)
    logro.activo = True
    logro.save()
    
    messages.success(request, f"El logro '{logro.descripcion}' ha sido reactivado correctamente.")
    return redirect('logros')