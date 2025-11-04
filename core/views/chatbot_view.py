from datetime import date
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Sum
from ..chatbot import chatbot
from ..models import Empleado, VacacionesSolicitud, DescuentoEmpleadoNomina, BeneficioEmpleadoNomina, EmpleadoCargo, CargoDepartamento


@csrf_exempt
def get_response_chatbot(request):
    if request.method != "POST":
        return JsonResponse({"response": "Método no permitido"}, status=405)

    data = json.loads(request.body)
    user_message = (data.get("message") or "").strip()
    user = request.user if request.user.is_authenticated else None

    text = user_message.lower()

    if "vacacion" in text or "vacaciones" in text or "días de vacaciones" in text:
        if not user or not user.is_authenticated:
            return JsonResponse({"response": "Para ver tus días de vacaciones debes iniciar sesión."})

        empleado = Empleado.objects.filter(usuario=user).first()
        if not empleado:
            return JsonResponse({"response": "No encontré tu registro de empleado. Contactá a RRHH."})

        total_disponibles = empleado.cantidad_dias_disponibles or 0

        usados = (
            VacacionesSolicitud.objects.filter(
                empleado=empleado,
                estado='aprobado',
                fecha_fin__lt=date.today()
            ).aggregate(total=Sum('cant_dias_solicitados'))['total'] or 0
        )

        pendientes = (
            VacacionesSolicitud.objects.filter(
                empleado=empleado,
                estado__in=['pendiente', 'aprobado'],
                fecha_inicio__gte=date.today()
            ).aggregate(total=Sum('cant_dias_solicitados'))['total'] or 0
        )

        disponibles = max(total_disponibles - usados - pendientes, 0)

        resp = (
            f"Tienes **{disponibles} días disponibles** de vacaciones. "
            f"(Total anual: {total_disponibles}, usados: {usados}, pendientes o programados: {pendientes})."
        )
        return JsonResponse({"response": resp})
    
    if "solicitud" in text or "estado" in text or "mis solicitudes" in text:
        if not user or not user.is_authenticated:
            return JsonResponse({"response": "Inicia sesión para ver tus solicitudes."})

        empleado = Empleado.objects.filter(usuario=user).first()
        if not empleado:
            return JsonResponse({"response": "No encontré tu registro de empleado."})

        total = VacacionesSolicitud.objects.filter(empleado=empleado).count()
        aprobadas = VacacionesSolicitud.objects.filter(empleado=empleado, estado='aprobado').count()
        pendientes = VacacionesSolicitud.objects.filter(empleado=empleado, estado='pendiente').count()
        rechazadas = VacacionesSolicitud.objects.filter(empleado=empleado, estado='rechazado').count()

        resp = (
            f"Tienes {total} solicitudes: {aprobadas} aprobadas, "
            f"{pendientes} pendientes y {rechazadas} rechazadas."
        )
        return JsonResponse({"response": resp})


    if "beneficio" in text or "beneficios" in text:
        if not user or not user.is_authenticated:
            return JsonResponse({"response": "Para consultar tus beneficios debes iniciar sesión."})

        empleado = Empleado.objects.filter(usuario=user).first()
        if not empleado:
            return JsonResponse({"response": "No encontré tu registro de empleado."})

        beneficios = (
            BeneficioEmpleadoNomina.objects
            .filter(empleado=empleado)
            .select_related('beneficio', 'nomina')
            .order_by('-nomina__fecha_pago')[:10]
        )

        if not beneficios.exists():
            return JsonResponse({"response": "Actualmente no tenés beneficios asignados."})

        lista_benef = []
        for b in beneficios:
            benef = b.beneficio
            valor = (
                f"${benef.monto}" if benef.monto
                else f"{benef.porcentaje}%"
                if benef.porcentaje else ""
            )
            lista_benef.append(f"• {benef.descripcion} ({valor})")

        respuesta = "Tus beneficios actuales son:\n" + "\n".join(lista_benef)
        return JsonResponse({"response": respuesta})

 
 
    if "descuento" in text or "retencion" in text or "deduccion" in text:
        if not user or not user.is_authenticated:
            return JsonResponse({"response": "Para consultar tus descuentos debes iniciar sesión."})

        empleado = Empleado.objects.filter(usuario=user).first()
        if not empleado:
            return JsonResponse({"response": "No encontré tu registro de empleado."})

        descuentos = (
            DescuentoEmpleadoNomina.objects
            .filter(empleado=empleado)
            .select_related('descuento', 'nomina')
            .order_by('-nomina__fecha_pago')[:10]
        )

        if not descuentos.exists():
            return JsonResponse({"response": "Actualmente no tenés descuentos registrados."})

        lista_desc = []
        for d in descuentos:
            desc = d.descuento
            valor = (
                f"${desc.monto}" if desc.monto
                else f"{desc.porcentaje}%"
                if desc.porcentaje else ""
            )
            lista_desc.append(f"• {desc.descripcion} ({valor})")

        respuesta = "Tus descuentos actuales son:\n" + "\n".join(lista_desc)
        return JsonResponse({"response": respuesta})


    if "cargo" in text:
        if not user or not user.is_authenticated:
            return JsonResponse({"response": "Inicia sesión para consultar tu cargo."})

        empleado = Empleado.objects.filter(usuario=user).first()
        if not empleado:
            return JsonResponse({"response": "No encontré tu registro de empleado."})

        if "actual" in text or "tengo" in text:
            cargo_actual = (
                EmpleadoCargo.objects.filter(empleado=empleado, fecha_fin__isnull=True)
                .select_related('cargo')
                .first()
            )
            if cargo_actual:
                return JsonResponse({"response": f"Tu cargo actual es **{cargo_actual.cargo.nombre}**."})
            return JsonResponse({"response": "Actualmente no tenés un cargo asignado."})

        if "tuve" in text or "anteriores" in text or "antes" in text:
            cargos_previos = (
                EmpleadoCargo.objects.filter(empleado=empleado, fecha_fin__isnull=False)
                .select_related('cargo')
            )
            if cargos_previos.exists():
                lista = ", ".join([c.cargo.nombre for c in cargos_previos])
                return JsonResponse({"response": f"Tuviste los siguientes cargos: {lista}."})
            return JsonResponse({"response": "No se registran cargos anteriores."})



    if "departamento" in text:
        if not user or not user.is_authenticated:
            return JsonResponse({"response": "Inicia sesión para consultar tu departamento."})

        empleado = Empleado.objects.filter(usuario=user).first()
        if not empleado:
            return JsonResponse({"response": "No encontré tu registro de empleado."})

        if "actual" in text or "tengo" in text:
            cargo_actual = (
                EmpleadoCargo.objects.filter(empleado=empleado, fecha_fin__isnull=True)
                .select_related('cargo')
                .first()
            )
            if cargo_actual:
                relacion = CargoDepartamento.objects.filter(cargo=cargo_actual.cargo).select_related('departamento').first()
                if relacion:
                    return JsonResponse({"response": f"Actualmente perteneces al departamento de **{relacion.departamento.nombre}**."})
            return JsonResponse({"response": "No se encontró un departamento asignado actualmente."})

        if "antes" in text or "anteriores" in text or "pertenecí" in text:
            cargos_previos = (
                EmpleadoCargo.objects.filter(empleado=empleado, fecha_fin__isnull=False)
                .select_related('cargo')
            )
            departamentos_previos = CargoDepartamento.objects.filter(
                cargo__in=[c.cargo for c in cargos_previos]
            ).select_related('departamento')

            if departamentos_previos.exists():
                lista = ", ".join({d.departamento.nombre for d in departamentos_previos})
                return JsonResponse({"response": f"Anteriormente perteneciste a los departamentos: {lista}."})
            return JsonResponse({"response": "No se registran departamentos anteriores."})



    bot_response = chatbot.get_response(user_message)
    return JsonResponse({"response": str(bot_response)})