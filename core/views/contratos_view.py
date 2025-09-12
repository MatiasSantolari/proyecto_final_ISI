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
    rol_actual = request.session.get("rol_actual", None)
    departamentos = None
    contratos = HistorialContrato.objects.filter(
        estado="activo"
        ).select_related("empleado", "cargo", "contrato").order_by('fecha_fin')

    historial_contratos = HistorialContrato.objects.all().select_related("empleado", "cargo", "contrato").order_by('-fecha_inicio')

    if rol_actual == "admin":
        departamentos = Departamento.objects.all()
        dep_id = request.GET.get("departamento")
        if dep_id:
            contratos = contratos.filter(cargo__cargodepartamento__departamento__id=dep_id)
            historial_contratos = historial_contratos.filter(cargo__cargodepartamento__departamento__id=dep_id)
    elif rol_actual in ["jefe", "gerente"]:
        empleado = request.user.empleado
        dep_id = empleado.cargos.first().departamento.id
        contratos = contratos.filter(cargo__cargodepartamento__departamento__id=dep_id)
        historial_contratos = historial_contratos.filter(cargo__cargodepartamento__departamento__id=dep_id)

    form = ContratoForm()
    return render(request, "contratos.html", {
        "contratos": contratos,
        "historial_contratos": historial_contratos,
        "form": form,
        "departamentos": departamentos,
        "rol_actual": rol_actual
    })



@login_required
def crear_contrato(request):
    if request.method == "POST":
        contrato_id = request.POST.get("id_contrato")
        renovar_flag = request.POST.get("renovar") == "true" 

        if contrato_id:
            contrato_ant = get_object_or_404(HistorialContrato, id=contrato_id)

            if renovar_flag:
                contrato_ant.estado = "renovado"
                contrato_ant.save()

                empleado = contrato_ant.empleado
                try:
                    cargo_actual = empleado.empleadocargo_set.get(fecha_fin__isnull=True)
                except EmpleadoCargo.DoesNotExist:
                    cargo_actual = empleado.empleadocargo_set.order_by('-fecha_inicio').first()

                tipo_id = request.POST.get("contrato")
                condiciones = request.POST.get("condiciones")
                monto = request.POST.get("monto_extra_pactado") or 0
                fecha_inicio = request.POST.get("fecha_inicio")
                fecha_fin = request.POST.get("fecha_fin")

                nuevo = HistorialContrato.objects.create(
                    empleado=empleado,
                    cargo=cargo_actual.cargo if cargo_actual else None,
                    contrato_id=tipo_id,
                    condiciones=condiciones,
                    monto_extra_pactado=monto,
                    estado="activo",
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin
                )

                messages.success(request, f"Contrato renovado correctamente. Nuevo contrato #{nuevo.id} generado.")
                return redirect("contratos")

            else:
                form = ContratoForm(request.POST, instance=contrato_ant)
                if form.is_valid():
                    contrato = form.save(commit=False)
                    try:
                        cargo_actual = contrato.empleado.empleadocargo_set.get(fecha_fin__isnull=True)
                    except EmpleadoCargo.DoesNotExist:
                        cargo_actual = contrato.empleado.empleadocargo_set.order_by('-fecha_inicio').first()
                    contrato.cargo = cargo_actual.cargo if cargo_actual else None
                    contrato.save()
                    messages.success(request, "Contrato editado correctamente.")
                    return redirect("contratos")
                else:
                    messages.error(request, "El formulario tiene errores.")
                    print("ERRORES DEL FORM:", form.errors)

        else:
            form = ContratoForm(request.POST)
            if form.is_valid():
                contrato = form.save(commit=False)
                try:
                    cargo_actual = contrato.empleado.empleadocargo_set.get(fecha_fin__isnull=True)
                except EmpleadoCargo.DoesNotExist:
                    cargo_actual = contrato.empleado.empleadocargo_set.order_by('-fecha_inicio').first()
                contrato.cargo = cargo_actual.cargo if cargo_actual else None
                contrato.estado = "activo"
                contrato.save()
                messages.success(request, "Contrato creado correctamente.")
                return redirect("contratos")
            else:
                messages.error(request, "El formulario tiene errores.")
                print("ERRORES DEL FORM:", form.errors)

    else:
        form = ContratoForm()

    return render(request, "contratos.html", {"form": form})



@login_required
def finalizar_contrato(request, contrato_id):
    contrato = get_object_or_404(HistorialContrato, id=contrato_id, estado="activo")
    if request.method == "POST":
        contrato.estado = "finalizado"
        contrato.save()
        messages.success(request, f"El contrato de {contrato.empleado.apellido} {contrato.empleado.nombre} fue finalizado antes de tiempo.")
        return redirect("contratos")

    return redirect("contratos")




@login_required
def mis_contratos(request):
    try:
        empleado = Empleado.objects.get(pk=request.user.persona.id)
    except Empleado.DoesNotExist:
        contratos = []
    else:
        contratos = HistorialContrato.objects.filter(
            empleado=empleado
        ).order_by("-fecha_inicio")

    return render(request, "mis_contratos.html", {
        "contratos": contratos,
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