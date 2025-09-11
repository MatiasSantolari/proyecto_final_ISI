from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from ..models import *
from ..forms import *
from django.views.decorators.http import require_POST
from datetime import timedelta
from dateutil.relativedelta import relativedelta



@login_required
def contratos(request):
    user = request.user
    form = ContratoForm()
    # Filtro según rol
    if user.rol == "admin":
        contratos = HistorialContrato.objects.filter(estado="activo")
        departamentos = Departamento.objects.all()
    else:
        contratos = HistorialContrato.objects.filter(estado="activo", empleado__departamento=user.empleado.departamento)
        departamentos = None
        form.fields['empleado'].queryset = Empleado.objects.filter(departamento=user.empleado.departamento)

    return render(request, "contratos.html", {
        "contratos": contratos,
        "form": form,
        "departamentos": departamentos
    })


@login_required
@require_POST
def crear_contrato(request):
    user = request.user
    form = ContratoForm(request.POST)

    if user.rol == "admin":
        form.fields['empleado'].queryset = Empleado.objects.all()
    else:
        dep = user.empleado.empleadocargo_set.first().cargo.cargodepartamento_set.first().departamento
        form.fields['empleado'].queryset = Empleado.objects.filter(
            empleadocargo__cargo__cargodepartamento__departamento=dep
        )

    if form.is_valid():
        contrato = form.save(commit=False)

        cargo_actual = contrato.empleado.empleadocargo_set.order_by("-fecha_asignacion").first()
        contrato.cargo = cargo_actual.cargo if cargo_actual else None

        contrato.estado = "activo"
        contrato.save()

        messages.success(request, f"Contrato para {contrato.empleado} creado correctamente.")
        return redirect("contratos")

    messages.error(request, "Error al crear el contrato. Verifica los datos.")
    return redirect("contratos")



@login_required
@require_POST
def editar_contrato(request, id_contrato):
    contrato = get_object_or_404(HistorialContrato, pk=id_contrato)
    form = ContratoForm(request.POST, instance=contrato)

    if form.is_valid():
        estado_anterior = contrato.estado
        contrato = form.save(commit=False)
        # si se renovó
        if contrato.estado == "renovado" and estado_anterior != "renovado":
            # crear nuevo registro
            nuevo = HistorialContrato.objects.create(
                empleado=contrato.empleado,
                tipo_contrato=contrato.tipo_contrato,
                fecha_inicio=contrato.fecha_fin,
                fecha_fin=contrato.tipo_contrato and contrato.fecha_fin or contrato.fecha_fin,
                condiciones=contrato.condiciones,
                monto_extra_pactado=contrato.monto_extra_pactado,
                estado="activo",
                cargo=contrato.cargo
            )
            contrato.estado = "renovado"
            contrato.save()
        else:
            contrato.save()

        messages.success(request, f"Contrato de {contrato.empleado} actualizado.")
        return redirect("contratos")
    
    messages.error(request, "Error al actualizar el contrato.")
    return redirect("contratos")





@login_required
def mis_contratos(request):
    contratos = HistorialContrato.objects.filter(empleado=request.user.persona.empleado)
    contrato_activo = contratos.filter(estado="activo").first()
    historial = contratos.exclude(estado="activo")

    return render(request, "mis_contratos.html", {
        "contrato_activo": contrato_activo,
        "historial": historial
    })






@login_required
def tipos_contrato(request):
    form = TipoContratoForm()
    tipos = TipoContrato.objects.all()
    return render(request, "tipos_contrato.html", {"form": form, "tipos": tipos})


@login_required
@require_POST
def crear_tipo_contrato(request):
    id_tipo = request.POST.get("id_tipo")
    if id_tipo:
        tipo = get_object_or_404(TipoContrato, pk=id_tipo)
        form = TipoContratoForm(request.POST, instance=tipo)
    else:
        form = TipoContratoForm(request.POST)

    if form.is_valid():
        tipo_guardado = form.save()
        if id_tipo:
            messages.success(request, f"Tipo de contrato '{tipo_guardado.descripcion}' actualizado correctamente.")
        else:
            messages.success(request, f"Tipo de contrato '{tipo_guardado.descripcion}' creado correctamente.")
        return redirect("tipos_contrato")
    else:
        messages.error(request, "Error al guardar. Verifica los datos.")
        tipos = TipoContrato.objects.all()
        return render(request, "tipos_contrato.html", {"form": form, "tipos": tipos})


@login_required
@require_POST
def eliminar_tipo_contrato(request, id_tipo):
    tipo = get_object_or_404(TipoContrato, pk=id_tipo)
    tipo.delete()
    messages.success(request, f"Tipo de contrato '{tipo.descripcion}' eliminado correctamente.")
    return redirect("tipos_contrato")