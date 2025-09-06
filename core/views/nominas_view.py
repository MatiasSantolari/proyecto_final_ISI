import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from datetime import date
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Subquery, OuterRef
from django.db.models import Case, When, IntegerField



@login_required
def generar_nominas(request):
    if request.method != "POST":
        messages.warning(request, "Debes confirmar la acción desde el botón correspondiente.")
        return redirect("nominas")

    accion = request.POST.get("accion")

    hoy = now().date()
    mes_actual = hoy.month
    anio_actual = hoy.year

    # Nóminas ya generadas este período
    nominas_existentes = Nomina.objects.filter(
        fecha_generacion__month=mes_actual,
        fecha_generacion__year=anio_actual
    )

    # Separar por estado
    nominas_pendientes = nominas_existentes.filter(estado="pendiente")
    nominas_pagadas = nominas_existentes.exclude(estado__in=["pendiente", "anulado"])
    nominas_anuladas = nominas_existentes.filter(estado="anulado")

    # Empleados con nómina pagada o pendiente (se excluyen del "generar")
    empleados_con_nomina_valida = list(
        nominas_pagadas.values_list("empleado_id", flat=True)
    ) + list(
        nominas_pendientes.values_list("empleado_id", flat=True)
    )

    empleados = Empleado.objects.all()

    empleados_a_generar = []  # empleados a los que se generará nómina
    empleados_sin_sueldo = []

    if accion == "regenerar":
        pendientes_count = nominas_pendientes.count()
        if pendientes_count == 0:
            messages.info(request, "No hay nóminas pendientes para regenerar.")
            return redirect("nominas")

        # Guardamos IDs de los pendientes en una lista antes de borrar
        empleados_ids = list(nominas_pendientes.values_list("empleado_id", flat=True))

        # Borramos solo las nóminas pendientes
        nominas_pendientes.delete()
        messages.warning(request, f"Se regenerarán {pendientes_count} nómina(s) pendientes.")

        # Recorremos solo esos empleados
        empleados = empleados.filter(id__in=empleados_ids)

    elif accion == "generar":
        # Solo los empleados que no tienen nómina en este periodo
        # o cuya última fue cancelada
        empleados_ids = [
            e.id for e in empleados
            if e.id not in empleados_con_nomina_valida
        ]
        empleados = empleados.filter(id__in=empleados_ids)

        if not empleados.exists():
            messages.info(request, "No hay empleados faltantes de nómina en este período.")
            return redirect("nominas")

    # Procesar empleados seleccionados
    for empleado in empleados:
        cargo_actual = empleado.empleadocargo_set.filter(
            fecha_inicio__lte=hoy,
            fecha_fin__isnull=True,
        ).order_by('-fecha_inicio').first()

        historial = None
        departamento = ""

        if cargo_actual:
            historial = cargo_actual.cargo.historialsueldobase_set.order_by("-fecha_sueldo").first()
            cargo_departamento_actual = cargo_actual.cargo.cargodepartamento_set.first()
            if cargo_departamento_actual:
                departamento = cargo_departamento_actual.departamento.nombre

        if historial:
            empleados_a_generar.append((empleado, historial.sueldo_base, departamento))
        else:
            empleados_sin_sueldo.append(empleado)

    # Generar las nóminas
    for empleado, sueldo_base, departamento in empleados_a_generar:
        bruto = sueldo_base
        total_descuentos = 0
        total_beneficios = 0

        # Descuentos fijos
        descuentos_fijos = Descuento.objects.filter(fijo=True, activo=True)
        for descuento in descuentos_fijos:
            if descuento.monto:
                total_descuentos += descuento.monto
            elif descuento.porcentaje:
                total_descuentos += (bruto * descuento.porcentaje) / 100

        # Descuentos específicos
        descuentos_asignados = DescuentoEmpleadoNomina.objects.filter(
            empleado=empleado,
            nomina__isnull=True,
            descuento__activo=True,
        )
        for de in descuentos_asignados:
            if de.descuento.monto:
                total_descuentos += de.descuento.monto
            elif de.descuento.porcentaje:
                total_descuentos += (bruto * de.descuento.porcentaje) / 100

        # Beneficios fijos
        beneficios_fijos = Beneficio.objects.filter(fijo=True, activo=True)
        for beneficio in beneficios_fijos:
            if beneficio.monto:
                total_beneficios += beneficio.monto
            elif beneficio.porcentaje:
                total_beneficios += (bruto * beneficio.porcentaje) / 100

        # Beneficios específicos
        beneficios_asignados = BeneficioEmpleadoNomina.objects.filter(
            empleado=empleado,
            nomina__isnull=True,
            beneficio__activo=True,
        )
        for be in beneficios_asignados:
            if be.beneficio.monto:
                total_beneficios += be.beneficio.monto
            elif be.beneficio.porcentaje:
                total_beneficios += (bruto * be.beneficio.porcentaje) / 100

        monto_neto = bruto - total_descuentos + total_beneficios
        numero = f"{empleado.id:06d}{hoy.month:02d}{str(hoy.year)[-2:]}"

        nomina = Nomina.objects.create(
            empleado=empleado,
            fecha_generacion=hoy,
            estado="pendiente",
            monto_bruto=bruto,
            monto_neto=monto_neto,
            total_descuentos=total_descuentos,
            total_beneficios=total_beneficios,
            numero=numero
        )

        for de in descuentos_asignados:
            de.nomina = nomina
            de.save()

        for be in beneficios_asignados:
            be.nomina = nomina
            be.save()

    # Mensajes finales
    if empleados_a_generar:
        if accion == "generar":
            messages.success(
                request,
                f"Se generaron correctamente {len(empleados_a_generar)} nómina(s) nuevas."
            )
        elif accion == "regenerar":
            messages.success(
                request,
                f"Se regeneraron correctamente {len(empleados_a_generar)} nómina(s) pendientes."
            )

    if empleados_sin_sueldo:
        nombres = ", ".join([f"{e.nombre} {e.apellido}" for e in empleados_sin_sueldo])
        messages.warning(
            request,
            f"Aún faltan {len(empleados_sin_sueldo)} empleado(s) sin sueldo cargado: {nombres}."
        )

    return redirect("nominas")




@login_required
def nominas(request):
    departamento_sel = request.GET.get('departamento', '')
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

    pendientes = nominas_list.filter(estado="pendiente").count()
    pagadas = nominas_list.exclude(estado=["pendiente","anulado"]).count()

    if departamento_sel:
        ultimo_cargo = (
            EmpleadoCargo.objects
            .filter(empleado=OuterRef('empleado'), fecha_fin__isnull=True)
            .order_by('-fecha_inicio')
            .values('cargo__cargodepartamento__departamento__nombre')[:1]
        )

        nominas_list = nominas_list.annotate(
            departamento_actual=Subquery(ultimo_cargo)
        ).filter(departamento_actual=departamento_sel)

    if mes:
        nominas_list = nominas_list.filter(fecha_generacion__month=int(mes))
    if anio:
        nominas_list = nominas_list.filter(fecha_generacion__year=int(anio))


     # Ordenar por periodo y estado
    estado_order = Case(
        When(estado="pendiente", then=1),
        When(estado="anulado", then=3),
        default=2,  # pagadas u otros
        output_field=IntegerField(),
    )

    nominas_list = nominas_list.annotate(
        estado_order=estado_order
    ).order_by(
        '-fecha_generacion__year',
        '-fecha_generacion__month',
        'estado_order'
    )


    # Faltantes por generar en el período actual
    hoy = now().date()
    mes_actual = hoy.month
    anio_actual = hoy.year

    nominas_periodo = Nomina.objects.filter(
        fecha_generacion__month=mes_actual,
        fecha_generacion__year=anio_actual
    )
    empleados_con_nomina = nominas_periodo.values_list("empleado_id", flat=True)
    faltantes = Empleado.objects.exclude(id__in=empleados_con_nomina).count()

    
    departamentos = Departamento.objects.all().order_by('nombre')

    return render(request, 'nominas.html', {
        'nominas': nominas_list,
        'meses': range(1, 13),
        'departamentos': departamentos,
        'departamento_sel': departamento_sel,
        'pendientes': pendientes,
        'pagadas': pagadas,
        'faltantes': faltantes,
    })



@login_required
def confirmar_nominas(request):
    if request.method != "POST":
        messages.warning(request, "Acción inválida.")
        return redirect("nominas")

    hoy = now().date()
    mes_actual = hoy.month
    anio_actual = hoy.year

    nominas_pendientes = Nomina.objects.filter(
        fecha_generacion__month=mes_actual,
        fecha_generacion__year=anio_actual,
        estado="pendiente"
    )

    count = nominas_pendientes.count()
    if count == 0:
        messages.info(request, "No hay nóminas pendientes para confirmar.")
        return redirect("nominas")

    nominas_pendientes.update(estado="pagado")
    messages.success(request, f"Se confirmaron {count} nómina(s) como pagadas.")

    return redirect("nominas")



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



@login_required
@require_POST
def anular_nomina(request, id_nomina):
    nomina = get_object_or_404(Nomina, pk=id_nomina)
    if nomina.estado == 'pendiente' or nomina.estado == 'pagado':
        nomina.estado = 'anulado'
        messages.success(request, "La nómina fue anulada correctamente.")
    else:
        nomina.estado = 'pendiente'
        messages.success(request, "La nómina fue restaurada correctamente.")
    nomina.save()
    return redirect('nominas')



@login_required
@require_POST
def eliminar_nomina(request, id_nomina):
    try:
        nomina = get_object_or_404(Nomina, id=id_nomina)
        nomina.delete()
        messages.success(request, "Nomina eliminada correctamente.")
    except Nomina.DoesNotExist:
        messages.error(request, "La nomina no existe.")
    return redirect('nominas')



@login_required
def ver_nomina(request, id_nomina):
    nomina = get_object_or_404(Nomina, id=id_nomina)

    # Descuentos asignados a la nómina
    descuentos = DescuentoEmpleadoNomina.objects.filter(nomina=nomina)
    descuentos_detalle = [
        {"descripcion": d.descuento.descripcion, 
         "monto": float(d.descuento.monto) if d.descuento.monto else 0, 
         "porcentaje": float(d.descuento.porcentaje*nomina.monto_bruto/100) if d.descuento.porcentaje else 0}
        for d in descuentos
    ]

    # Agregar descuentos fijos
    descuentos_fijos = Descuento.objects.filter(fijo=True)
    for df in descuentos_fijos:
        descuentos_detalle.append({
            "descripcion": df.descripcion + " (fijo)",
            "monto": float(df.monto) if df.monto else 0,
            "porcentaje": float(df.porcentaje*nomina.monto_bruto/100) if df.porcentaje else 0
        })

    # Beneficios asignados a la nómina
    beneficios = BeneficioEmpleadoNomina.objects.filter(nomina=nomina)
    beneficios_detalle = [
        {"descripcion": b.beneficio.descripcion, 
        "monto": float(b.beneficio.monto) if b.beneficio.monto else 0, 
        "porcentaje": float(b.beneficio.porcentaje*nomina.monto_bruto/100) if b.beneficio.porcentaje else 0}
        for b in beneficios
    ]

    # Agregar beneficios fijos
    beneficios_fijos = Beneficio.objects.filter(fijo=True)
    for be in beneficios_fijos:
        beneficios_detalle.append({
            "descripcion": be.descripcion + " (fijo)",
            "monto": float(be.monto) if be.monto else 0,
            "porcentaje": float(be.porcentaje*nomina.monto_bruto/100) if be.porcentaje else 0
        })

    data = {
        "empleado": f"{nomina.empleado.nombre} {nomina.empleado.apellido}",
        "dni": nomina.empleado.dni,
        "cargo": nomina.empleado.cargo_actual_nombre(),  
        "departamento": nomina.empleado.departamento_actual_nombre(),
        "fecha_generacion": nomina.fecha_generacion.strftime("%d/%m/%Y"),
        "fecha_pago": nomina.fecha_pago.strftime("%d/%m/%Y") if nomina.fecha_pago else None,
        "monto_bruto": float(nomina.monto_bruto),
        "monto_neto": float(nomina.monto_neto),
        "total_descuentos": float(nomina.total_descuentos),
        "descuentos_detalle": descuentos_detalle,
        "beneficios_detalle": beneficios_detalle,
        "numero": nomina.numero,
        "estado": nomina.estado,
    }
    return JsonResponse(data)