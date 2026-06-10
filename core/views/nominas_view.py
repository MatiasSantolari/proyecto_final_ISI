from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from datetime import date
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.db.models import Subquery, OuterRef
from django.db.models import Case, When, IntegerField, Sum, Subquery, OuterRef, Q
from django.core.paginator import Paginator
from decimal import Decimal
import io
import os
from django.template.loader import render_to_string
from xhtml2pdf import pisa 


@login_required
def generar_nominas(request):
    if request.method != "POST":
        messages.warning(request, "Debes confirmar la acción desde el botón correspondiente.")
        return redirect("nominas")

    accion = request.POST.get("accion")

    hoy = now().date()
    mes_actual = hoy.month
    anio_actual = hoy.year

    nominas_existentes = Nomina.objects.filter(
        fecha_generacion__month=mes_actual,
        fecha_generacion__year=anio_actual
    )

    nominas_pendientes = nominas_existentes.filter(estado__iexact="pendiente")
    nominas_pagadas = nominas_existentes.exclude(estado__in=["pendiente", "anulado"])

    empleados_con_nomina_valida = list(
        nominas_pagadas.values_list("empleado_id", flat=True)
    ) + list(
        nominas_pendientes.values_list("empleado_id", flat=True)
    )

    empleados = Empleado.objects.filter(estado="activo")

    empleados_a_generar = []
    empleados_sin_sueldo = []
    empleados_sin_contrato = []

    if accion == "regenerar":
        pendientes_count = nominas_pendientes.count()
        if pendientes_count == 0:
            messages.info(request, "No hay nóminas pendientes para regenerar.")
            return redirect("nominas")

        empleados_ids = list(nominas_pendientes.values_list("empleado_id", flat=True))

        nominas_pendientes.delete()
        messages.warning(request, f"Se regenerarán {pendientes_count} nómina(s) pendientes.")

        empleados = empleados.filter(id__in=empleados_ids)

    elif accion == "generar":
        empleados_ids = [
            e.id for e in empleados
            if e.id not in empleados_con_nomina_valida
        ]
        empleados = empleados.filter(id__in=empleados_ids)

        if not empleados.exists():
            messages.info(request, "No hay empleados faltantes de nómina en este período.")
            return redirect("nominas")

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

        contrato_vigente = HistorialContrato.objects.filter(
            Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True),
            empleado=empleado,
            estado__in=["activo", "renovado"],
            fecha_inicio__lte=hoy,
        ).order_by('fecha_inicio').first()


        if contrato_vigente:
            if historial:
                empleados_a_generar.append((empleado, historial.sueldo_base, departamento, historial))
            else:
                empleados_sin_sueldo.append(empleado)
        else:
            empleados_sin_contrato.append(empleado)

    for empleado, sueldo_base, departamento, historial_obj in empleados_a_generar:
        sueldo_base_dec = Decimal(str(sueldo_base))
        total_descuentos = Decimal('0.00')
        total_beneficios = Decimal('0.00')
        monto_extra_dec = Decimal('0.00')

        fecha_inicio_periodo = date(anio_actual, mes_actual, 1)

        if mes_actual == 12:
            fecha_fin_periodo = date(anio_actual, 12, 31)
        else:
            fecha_fin_periodo = date(anio_actual, mes_actual + 1, 1) - timedelta(days=1)

        contrato_vigente = HistorialContrato.objects.filter(
            Q(fecha_fin__gte=fecha_inicio_periodo) | Q(fecha_fin__isnull=True),
            empleado=empleado,
            estado__in=["activo", "renovado"],
            fecha_inicio__lte=fecha_fin_periodo
        ).order_by('fecha_inicio').first()

        if contrato_vigente and contrato_vigente.monto_extra_pactado:
            monto_extra_dec = Decimal(str(contrato_vigente.monto_extra_pactado))

        base_calculo = sueldo_base_dec + monto_extra_dec

        beneficios_fijos = Beneficio.objects.filter(fijo=True, activo=True)
        for beneficio in beneficios_fijos:
            if beneficio.monto:
                total_beneficios += beneficio.monto
            elif beneficio.porcentaje:
                total_beneficios += (base_calculo * beneficio.porcentaje) / Decimal('100.00')

        beneficios_asignados = BeneficioEmpleadoNomina.objects.filter(
            empleado=empleado,
            nomina__isnull=True,
            beneficio__activo=True,
        )
        for be in beneficios_asignados:
            if be.beneficio.monto:
                total_beneficios += be.beneficio.monto
            elif be.beneficio.porcentaje:
                total_beneficios += (base_calculo * be.beneficio.porcentaje) / Decimal('100.00')

        descuentos_fijos = Descuento.objects.filter(fijo=True, activo=True)
        for descuento in descuentos_fijos:
            if descuento.monto:
                total_descuentos += descuento.monto
            elif descuento.porcentaje:
                total_descuentos += (base_calculo * descuento.porcentaje) / Decimal('100.00')

        descuentos_asignados = DescuentoEmpleadoNomina.objects.filter(
            empleado=empleado,
            nomina__isnull=True,
            descuento__activo=True,
        )
        for de in descuentos_asignados:
            if de.descuento.monto:
                total_descuentos += de.descuento.monto
            elif de.descuento.porcentaje:
                total_descuentos += (base_calculo * de.descuento.porcentaje) / Decimal('100.00')

        monto_bruto = base_calculo + total_beneficios
        monto_neto = monto_bruto - total_descuentos

        numero = f"{empleado.id:06d}{hoy.month:02d}{str(hoy.year)[-2:]}"

        nomina = Nomina.objects.create(
            empleado=empleado,
            fecha_generacion=hoy,
            estado="pendiente",
            monto_bruto=monto_bruto,
            monto_neto=monto_neto,
            total_descuentos=total_descuentos,
            total_beneficios=total_beneficios,
            numero=numero,
            monto_extra_pactado=monto_extra_dec
        )

        if historial_obj:
            nomina.historial_sueldos.add(historial_obj)

        descuentos_asignados.update(nomina=nomina)
        beneficios_asignados.update(nomina=nomina)

        DescuentoEmpleadoNomina.objects.filter(empleado=empleado, nomina__isnull=True, descuento__activo=False).delete()
        BeneficioEmpleadoNomina.objects.filter(empleado=empleado, nomina__isnull=True, beneficio__activo=False).delete()

    if empleados_a_generar:
        if accion == "generar":
            messages.success(request, f"Se generaron correctamente {len(empleados_a_generar)} nómina(s) nuevas.")
        elif accion == "regenerar":
            messages.success(request, f"Se regeneraron correctamente {len(empleados_a_generar)} nómina(s) pendientes.")

    if empleados_sin_sueldo:
        nombres = ", ".join([f"{e.nombre} {e.apellido}" for e in empleados_sin_sueldo])
        messages.warning(request, f"Aún faltan {len(empleados_sin_sueldo)} empleado(s) sin sueldo cargado: {nombres}.")

    if empleados_sin_contrato:
        nombres = ", ".join([f"{e.nombre} {e.apellido}" for e in empleados_sin_contrato])
        messages.warning(request, f"{len(empleados_sin_contrato)} empleado(s) no tienen contrato vigente: {nombres}.")

    return redirect("nominas")




@login_required
def nominas(request):
    departamento_sel = request.GET.get('departamento', '')
    mes = request.GET.get('mes', '')
    anio = request.GET.get('anio', '')

    if not mes or not anio:
        ultima_nomina = Nomina.objects.order_by('-fecha_generacion').first()
        if ultima_nomina:
            if not mes: mes = str(ultima_nomina.fecha_generacion.month)
            if not anio: anio = str(ultima_nomina.fecha_generacion.year)
        else:
            hoy_fecha = now().date()
            if not mes: mes = str(hoy_fecha.month)
            if not anio: anio = str(hoy_fecha.year)

    mes = str(mes)
    anio = str(anio)

    nominas_list = (
        Nomina.objects
        .select_related('empleado')
        .prefetch_related(
            'empleado__empleadocargo_set__cargo__cargodepartamento_set__departamento'
        )
        .all()
    )

    if mes:
        nominas_list = nominas_list.filter(fecha_generacion__month=int(mes))

    if anio:
        nominas_list = nominas_list.filter(fecha_generacion__year=int(anio))

    pendientes = nominas_list.filter(estado__iexact="pendiente").count()
    pagadas = nominas_list.exclude(estado__in=["pendiente", "anulado"]).count()

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

    nominas_validas = nominas_list.exclude(estado__iexact="anulado")
    gasto_total_resultado = nominas_validas.aggregate(total_gastos=Sum('monto_bruto'))
    gasto_total_empresa = gasto_total_resultado['total_gastos'] or Decimal('0.00')

    estado_order = Case(
        When(estado__iexact="pendiente", then=1),
        When(estado__iexact="anulado", then=3),
        default=2,
        output_field=IntegerField(),
    )

    nominas_list = nominas_list.annotate(
        estado_order=estado_order
    ).order_by(
        '-fecha_generacion__year',
        '-fecha_generacion__month',
        'estado_order'
    )

    paginator = Paginator(nominas_list, 10)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    rango_paginas = paginator.get_elided_page_range(page_number, on_each_side=2, on_ends=1)

    nominas_periodo = Nomina.objects.filter(
        fecha_generacion__month=int(mes),
        fecha_generacion__year=int(anio)
    )
    empleados_con_nomina = nominas_periodo.values_list("empleado_id", flat=True)
    faltantes = Empleado.objects.exclude(id__in=empleados_con_nomina).count()

    departamentos = Departamento.objects.all().order_by('nombre')

    mostrar_boton_regreso = 'from_detalle' in request.GET
    url_regreso = request.META.get('HTTP_REFERER', '#')

    nombres_meses = {
        "1": "Enero", "2": "Febrero", "3": "Marzo", "4": "Abril", "5": "Mayo", "6": "Junio",
        "7": "Julio", "8": "Agosto", "9": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
    }
    texto_periodo_actual = f"{nombres_meses.get(mes, 'Mes ' + mes)} {anio}"

    return render(request, 'nominas.html', {
        'nominas': page_obj,
        'page_obj': page_obj,
        'rango_paginas': rango_paginas,
        'meses': range(1, 13),
        'departamentos': departamentos,
        'departamento_sel': departamento_sel,
        'mes_seleccionado': mes,
        'anio_seleccionado': anio,
        'texto_periodo_actual': texto_periodo_actual,
        'pendientes': pendientes,
        'pagadas': pagadas,
        'faltantes': faltantes,
        'gasto_total_empresa': gasto_total_empresa,
        'mostrar_boton_regreso': mostrar_boton_regreso,
        'url_regreso': url_regreso,
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
        estado__iexact="pendiente"
    )

    count = nominas_pendientes.count()
    if count == 0:
        messages.info(request, "No hay nóminas pendientes para confirmar.")
        return redirect("nominas")

    nominas_pendientes.update(estado="pagado", fecha_pago=hoy)
    messages.success(request, f"Se confirmaron {count} nómina(s) como pagadas.")

    return redirect("nominas")




@login_required
@require_POST
def editar_nomina(request):
    id_nomina = request.POST.get('id_nomina')

    if id_nomina:
        nomina = get_object_or_404(Nomina, pk=id_nomina)
        if nomina.estado.lower() != "pendiente":
            messages.error(request, "No se pueden editar liquidaciones confirmadas o anuladas.")
            return redirect("nominas")
        form = NominaForm(request.POST, instance=nomina)
    else:
        form = NominaForm(request.POST)

    if form.is_valid():
        form.save()
        messages.success(request, "Nómina actualizada correctamente.")
        return redirect('nominas')

    nominasList = Nomina.objects.all().order_by('-fecha_generacion')
    return render(request, 'nominas.html', {'form': form, 'nominas': nominasList})




@login_required
@require_POST
def anular_nomina(request, id_nomina):
    nomina = get_object_or_404(Nomina, pk=id_nomina)
    
    if nomina.estado.lower() == 'pagado':
        messages.error(request, "ERROR CRÍTICO: Una liquidación confirmada y PAGADA no puede ser alterada.")
        return redirect('nominas')

    if nomina.estado.lower() == 'pendiente':
        nomina.estado = 'Anulado' 
        messages.success(request, "La nómina fue anulada correctamente.")
    else:
        nomina.estado = 'pendiente'
        messages.success(request, "La nómina fue restaurada al estado pendiente.")
        
    nomina.save()
    return redirect('nominas')




@login_required
@require_POST
def eliminar_nomina(request, id_nomina):
    try:
        nomina = get_object_or_404(Nomina, id=id_nomina)
        nomina.delete()
        messages.success(request, "Nómina eliminada correctamente.")
    except Nomina.DoesNotExist:
        messages.error(request, "La nómina no existe.")
    return redirect('nominas')




@login_required
def ver_nomina(request, id_nomina):
    nomina = get_object_or_404(Nomina, id=id_nomina)

    base_calculo = nomina.monto_bruto - nomina.total_beneficios
    base_calc_dec = Decimal(str(base_calculo))

    descuentos_detalle = []
    acumulador_descuentos_real = Decimal('0.00')

    descuentos_variables = DescuentoEmpleadoNomina.objects.filter(nomina=nomina)
    for d in descuentos_variables:
        monto_pesos = Decimal('0.00')
        if d.descuento.monto is not None:
            monto_pesos = d.descuento.monto
        elif d.descuento.porcentaje is not None:
            monto_pesos = base_calc_dec * (d.descuento.porcentaje / Decimal('100.00'))

        acumulador_descuentos_real += monto_pesos
        descuentos_detalle.append({
            "descripcion": d.descuento.descripcion,
            "monto_final": float(monto_pesos)
        })

    descuentos_fijos = Descuento.objects.filter(fijo=True)
    for df in descuentos_fijos:
        monto_pesos = Decimal('0.00')
        if df.monto is not None:
            monto_pesos = df.monto
        elif df.porcentaje is not None:
            monto_pesos = base_calc_dec * (df.porcentaje / Decimal('100.00'))

        acumulador_descuentos_real += monto_pesos
        descuentos_detalle.append({
            "descripcion": f"{df.descripcion} (fijo)",
            "monto_final": float(monto_pesos)
        })


    beneficios_detalle = []
    acumulador_beneficios_real = Decimal('0.00')

    beneficios_variables = BeneficioEmpleadoNomina.objects.filter(nomina=nomina)
    for b in beneficios_variables:
        monto_pesos = Decimal('0.00')
        if b.beneficio.monto is not None:
            monto_pesos = b.beneficio.monto
        elif b.beneficio.porcentaje is not None:
            monto_pesos = base_calculo * (b.beneficio.porcentaje / Decimal('100.00'))

        acumulador_beneficios_real += monto_pesos
        beneficios_detalle.append({
            "descripcion": b.beneficio.descripcion,
            "monto_final": float(monto_pesos)
        })

    beneficios_fijos = Beneficio.objects.filter(fijo=True)
    for be in beneficios_fijos:
        monto_pesos = Decimal('0.00')
        if be.monto is not None:
            monto_pesos = be.monto
        elif be.porcentaje is not None:
            monto_pesos = base_calculo * (be.porcentaje / Decimal('100.00'))

        acumulador_beneficios_real += monto_pesos
        beneficios_detalle.append({
            "descripcion": f"{be.descripcion} (fijo)",
            "monto_final": float(monto_pesos)
        })

    base_contractual_pura = Decimal(str(nomina.monto_bruto)) - Decimal(str(nomina.total_beneficios))

    monto_bruto_real = base_contractual_pura + acumulador_beneficios_real
    monto_neto_real = monto_bruto_real - acumulador_descuentos_real

    return JsonResponse({
        "empleado": f"{nomina.empleado.nombre} {nomina.empleado.apellido}",
        "dni": nomina.empleado.dni,
        "cargo": nomina.empleado.cargo_actual_nombre(),
        "departamento": nomina.empleado.departamento_actual_nombre(),
        "fecha_generacion": nomina.fecha_generacion.strftime("%d/%m/%Y"),
        "fecha_pago": nomina.fecha_pago.strftime("%d/%m/%Y") if nomina.fecha_pago else None,
        "monto_bruto": float(monto_bruto_real),
        "monto_neto": float(monto_neto_real),
        "total_descuentos": float(acumulador_descuentos_real),
        "total_beneficios": float(acumulador_beneficios_real),   
        "descuentos_detalle": descuentos_detalle,
        "beneficios_detalle": beneficios_detalle,
        "numero": nomina.numero,
        "estado": nomina.estado,
        "monto_extra_pactado": float(nomina.monto_extra_pactado if nomina.monto_extra_pactado else 0.0),
    })




@login_required
def mis_nominas(request):
    persona_usuario = getattr(request.user, 'persona', None)
    
    empleado = None
    if persona_usuario:
        empleado = Empleado.objects.filter(id=persona_usuario.id).first()

    if not empleado:
        return render(request, "mis_nominas.html", {
            "nominas": [],
            "error": "No hay un perfil de empleado asociado a este usuario para consultar recibos."
        })

    nominas_list = (
        Nomina.objects
        .filter(empleado=empleado, estado__iexact="pagado")
        .select_related("empleado")
        .prefetch_related("empleado__datos_bancarios") 
        .order_by("-fecha_generacion")
    )

    paginator = Paginator(nominas_list, 10)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    return render(request, "mis_nominas.html", {
        "nominas": page_obj,
    })




@login_required
def exportar_recibo_pdf(request, id_nomina):
    nomina = get_object_or_404(Nomina, id=id_nomina)
    
    if not request.user.is_staff and nomina.empleado.id != request.user.persona.id:
        return HttpResponse("Acceso denegado de seguridad.", status=403)

    historial_sueldo = nomina.historial_sueldos.first()
    sueldo_base = historial_sueldo.sueldo_base if historial_sueldo else Decimal('0.00')
    monto_extra = nomina.monto_extra_pactado if nomina.monto_extra_pactado else Decimal('0.00')
    base_calculo = sueldo_base + monto_extra

    conceptos_recibo = []

    conceptos_recibo.append({
        "codigo": "001",
        "descripcion": "Sueldo Básico de Convenio",
        "porcentaje_unidades": "30 Días",
        "haberes": float(sueldo_base),
        "descuentos": None
    })

    if monto_extra > 0:
        conceptos_recibo.append({
            "codigo": "005",
            "descripcion": "Monto Extra Pactado Contractual",
            "porcentaje_unidades": "-",
            "haberes": float(monto_extra),
            "descuentos": None
        })

    beneficios_variables = BeneficioEmpleadoNomina.objects.filter(nomina=nomina)
    for b in beneficios_variables:
        monto = b.beneficio.monto
        porc = f"{b.beneficio.porcentaje}%" if b.beneficio.porcentaje else "-"
        if b.beneficio.porcentaje:
            monto = base_calculo * (b.beneficio.porcentaje / Decimal('100.00'))
        
        conceptos_recibo.append({
            "codigo": f"B{b.beneficio.id:02d}",
            "descripcion": b.beneficio.descripcion,
            "porcentaje_unidades": porc,
            "haberes": float(monto),
            "descuentos": None
        })

    beneficios_fijos = Beneficio.objects.filter(fijo=True)
    for be in beneficios_fijos:
        if not beneficios_variables.filter(beneficio=be).exists():
            monto = be.monto
            porc = f"{be.porcentaje}%" if be.porcentaje else "-"
            if be.porcentaje:
                monto = base_calculo * (be.porcentaje / Decimal('100.00'))
            conceptos_recibo.append({
                "codigo": f"BF{be.id:02d}",
                "descripcion": be.descripcion,
                "porcentaje_unidades": porc,
                "haberes": float(monto),
                "descuentos": None
            })

    descuentos_variables = DescuentoEmpleadoNomina.objects.filter(nomina=nomina)
    for d in descuentos_variables:
        monto = d.descuento.monto
        porc = f"{d.descuento.porcentaje}%" if d.descuento.porcentaje else "-"
        if d.descuento.porcentaje:
            monto = base_calculo * (d.descuento.porcentaje / Decimal('100.00'))
        
        conceptos_recibo.append({
            "codigo": f"D{d.descuento.id:02d}",
            "descripcion": d.descuento.descripcion,
            "porcentaje_unidades": porc,
            "haberes": None,
            "descuentos": float(monto)
        })

    descuentos_fijos = Descuento.objects.filter(fijo=True)
    for df in descuentos_fijos:
        if not descuentos_variables.filter(descuento=df).exists():
            monto = df.monto
            porc = f"{df.porcentaje}%" if df.porcentaje else "-"
            if df.porcentaje:
                monto = base_calculo * (df.porcentaje / Decimal('100.00'))
            conceptos_recibo.append({
                "codigo": f"DF{df.id:02d}",
                "descripcion": df.descripcion,
                "porcentaje_unidades": porc,
                "haberes": None,
                "descuentos": float(monto)
            })

    context = {
        "nomina": nomina,
        "empleado": nomina.empleado,
        "conceptos": conceptos_recibo,
        "periodo": nomina.fecha_generacion.strftime("%B %Y").upper(),
        "fecha_impresion": date.today().strftime("%d/%m/%Y"),
        "cargo": nomina.empleado.cargo_actual_nombre(),
        "departamento": nomina.empleado.departamento_actual_nombre(),
    }

    html_string = render_to_string("recibo_sueldo_pdf.html", context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recibo_{nomina.numero}.pdf"'
    
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Ocurrió un error al compilar el recibo oficial.', status=500)
    return response




@login_required
def exportar_pago_bancario_txt(request):
    mes = request.GET.get('mes', '').strip()
    anio = request.GET.get('anio', '').strip()
    
    if not mes or not anio:
        ultima_nomina = Nomina.objects.order_by('-fecha_generacion').first()
        if ultima_nomina:
            mes = str(ultima_nomina.fecha_generacion.month)
            anio = str(ultima_nomina.fecha_generacion.year)
        else:
            fecha_hoy = date.today()
            mes = str(fecha_hoy.month)
            anio = str(fecha_hoy.year)

    nominas_a_pagar = Nomina.objects.filter(
        fecha_generacion__month=int(mes), 
        fecha_generacion__year=int(anio)  
    ).exclude(estado__iexact="anulado").select_related('empleado')

    buffer = io.StringIO()
    cuit_empresa = "30711122233" 

    for nomina in nominas_a_pagar:
        empleado = nomina.empleado
        
        if hasattr(empleado, 'datos_bancarios') and empleado.datos_bancarios.cbu_cuenta:
            cbu_destino = empleado.datos_bancarios.cbu_cuenta.zfill(22)
        else:
            cbu_destino = "0000000000000000000000"

        cuil_empleado = empleado.dni.zfill(11) 

        monto_centavos = int(nomina.monto_neto * 100)
        monto_formateado = str(monto_centavos).zfill(13)

        linea = f"{cuit_empresa}{cbu_destino}{monto_formateado},{cuil_empleado}\n"
        buffer.write(linea)

    response = HttpResponse(buffer.getvalue(), content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="pago_haberes_{mes}_{anio}.txt"'
    return response
