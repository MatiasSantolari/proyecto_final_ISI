from datetime import date
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from django.db.models import Sum
from ...models import *
from pydantic import BaseModel, Field 
from datetime import date, timedelta, datetime


class GenericUserIDInput(BaseModel):
    """Input simple que requiere solo el user_id para realizar una consulta."""
    user_id: int = Field(description="El ID del usuario autenticado actual.")


@tool("get_vacation_days", args_schema=GenericUserIDInput)
def get_vacation_days_tool(user_id: int) -> str: 
    """Calcula y devuelve los días de vacaciones disponibles, usados y pendientes del empleado logueado."""

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "ERROR: No se encontró el registro de empleado."

    total_disponibles = empleado.cantidad_dias_disponibles or 0
    usados = (VacacionesSolicitud.objects.filter(empleado=empleado, estado='aprobado', fecha_fin__lt=date.today()).aggregate(total=Sum('cant_dias_solicitados'))['total'] or 0)
    pendientes = (VacacionesSolicitud.objects.filter(empleado=empleado, estado__in=['pendiente', 'aprobado'], fecha_inicio__gte=date.today()).aggregate(total=Sum('cant_dias_solicitados'))['total'] or 0)
    disponibles = max(total_disponibles - usados - pendientes, 0)
    
    if disponibles > 0:
        final_response = (f"¡Hola! 😄 Tienes **{disponibles} días disponibles** para viajar. "
                f"Aquí está el detalle de tu información:\n\n"
                f"• Total anual asignado: {total_disponibles} días\n"
                f"• Días ya utilizados: {usados} días\n"
                f"• Días pendientes/programados: {pendientes} días\n\n"
                f"¡Planifica ese descanso! ✈️")
    else:
        final_response =  (f"Hola. Actualmente no te quedan días de vacaciones disponibles para solicitar. 😔\n\n"
                f"• Total anual asignado: {total_disponibles} días\n"
                f"• Días ya utilizados: {usados} días\n"
                f"• Días pendientes/programados: {pendientes} días")
    return final_response

@tool("get_benefits", args_schema=GenericUserIDInput)
def get_benefits_tool(user_id: int) -> str:
    """Busca y lista los beneficios actuales del empleado asociado al user_id."""
    
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "ERROR: No se encontró el registro de empleado."

    beneficios = BeneficioEmpleadoNomina.objects.filter(empleado=empleado).order_by('-nomina__fecha_pago')[:10]
    if not beneficios.exists(): 
        return "😔 Vaya, parece que actualmente no tenés beneficios asignados en el sistema."

    lista_benef = []
    for b in beneficios:
        valor = f"${b.beneficio.monto}" if b.beneficio.monto else (f"{b.beneficio.porcentaje}%" if b.beneficio.porcentaje else "")
        lista_benef.append(f"• **{b.beneficio.descripcion}** ({valor})")
        
    return (f"¡Buenas noticias! ✨ Estos son tus beneficios actuales:\n\n" + 
            "\n".join(lista_benef) + 
            "\n\nSi tienes dudas sobre su uso, contacta con el equipo de RRHH.")



@tool("get_discounts", args_schema=GenericUserIDInput)
def get_discounts_tool(user_id: int) -> str:
    """Busca y lista los descuentos/retenciones recientes del empleado."""
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "ERROR: No se encontró el registro de empleado."

    descuentos = DescuentoEmpleadoNomina.objects.filter(empleado=empleado).order_by('-nomina__fecha_pago')[:10]
    
    if not descuentos.exists(): 
        return "✅ ¡Estás de suerte! Actualmente no tenés descuentos registrados en tus últimas nóminas."
        
    lista_desc = []
    for d in descuentos:
        valor = f"${d.descuento.monto}" if d.descuento.monto else (f"{d.descuento.porcentaje}%" if d.descuento.porcentaje else "")
        lista_desc.append(f"• **{d.descuento.descripcion}** ({valor})")
        
    return (f"Hola. Estos son los descuentos/retenciones que figuran en tus últimas nóminas:\n\n" + 
            "\n".join(lista_desc) +
            "\n\nPara más detalles, revisa tu recibo de sueldo digital.")



@tool("get_current_role_and_department", args_schema=GenericUserIDInput)
def get_current_role_and_department_tool(user_id: int) -> str:
    """Obtiene el cargo y departamento actual del empleado."""
    empleado = Empleado.objects.filter(usuario_id=user_id).first()
    if not empleado: return "ERROR: No se encontró el registro de empleado."

    cargo_actual = EmpleadoCargo.objects.filter(empleado=empleado, fecha_fin__isnull=True).select_related('cargo').first()
    
    if cargo_actual:
        relacion = CargoDepartamento.objects.filter(cargo=cargo_actual.cargo).select_related('departamento').first()
        depto = relacion.departamento.nombre if relacion else "No asignado"
        
        return (f"Actualmente, tu información de puesto es la siguiente:\n"
                f"🔧 **Cargo:** **{cargo_actual.cargo.nombre}**\n"
                f"🏢 **Departamento:** {depto}\n\n"
                f"¡Gracias por tu trabajo en {depto}! 🎉")
        
    return "😔 No se encontró un cargo o departamento asignado actualmente en el sistema."



@tool("get_employee_objectives", args_schema=GenericUserIDInput)
def get_employee_objectives_tool(user_id: int) -> str:
    """Busca y lista los objetivos actuales y completados del empleado."""
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "ERROR: No se encontró tu registro de empleado."

    objetivos_activos = ObjetivoEmpleado.objects.filter(empleado=empleado, completado=False).select_related('objetivo').order_by('fecha_limite')
    objetivos_completados = ObjetivoEmpleado.objects.filter(empleado=empleado, completado=True).select_related('objetivo').order_by('-fecha_asignacion')[:5]

    response_parts = []

    if objetivos_activos.exists():
        response_parts.append("🎯 **Tus objetivos activos:**")
        for oe in objetivos_activos:
            titulo = oe.objetivo.titulo
            limite = oe.fecha_limite.strftime('%d/%m/%Y') if oe.fecha_limite else 'Sin límite'
            response_parts.append(f"• **{titulo}** (Límite: {limite})")
        response_parts.append("\n")
    
    if objetivos_completados.exists():
        response_parts.append("✅ **Completados recientemente:**")
        for oe in objetivos_completados:
            response_parts.append(f"• {oe.objetivo.titulo}")
        response_parts.append("\n")

    if not objetivos_activos.exists() and not objetivos_completados.exists():
        return "😔 Actualmente no tienes objetivos asignados en el sistema."

    return "\n".join(response_parts)



@tool("get_last_payroll", args_schema=GenericUserIDInput)
def get_last_payroll_tool(user_id: int) -> str:
    """Busca y devuelve los detalles de la última nómina (recibo de sueldo) del empleado, incluyendo montos netos, brutos, beneficios y descuentos."""
    
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: 
        return "ERROR: No se encontró el registro de empleado asociado a este usuario."

    last_payroll = Nomina.objects.filter(
        empleado=empleado
    ).order_by('-fecha_pago').first()

    if not last_payroll:
        return "😔 Vaya, parece que no hay registros de nóminas anteriores para mostrar."

    fecha_pago_str = last_payroll.fecha_pago.strftime("%d/%m/%Y") if last_payroll.fecha_pago else "N/A"
    
    response_text = (
        f"Aquí están los detalles de tu última nómina (liquidación):\n\n"
        f"🔢 **Período/Número:** {last_payroll.numero or 'N/A'}\n"
        f"📅 **Fecha de Pago:** {fecha_pago_str}\n\n"
        
        f"--- Resumen Financiero ---\n\n"        
        f"💰 **Total Bruto:** ${last_payroll.monto_bruto}\n"
        f"✨ **Total Beneficios:** ${last_payroll.total_beneficios}\n"
        f"➖ **Total Descuentos:** ${last_payroll.total_descuentos}\n\n"

        f"💸 **Monto Neto (A cobrar):** **${last_payroll.monto_neto}**\n\n"
        f"--------------------------"
    )
    return response_text



@tool("get_last_performance_review", args_schema=GenericUserIDInput)
def get_last_performance_review_tool(user_id: int) -> str:
    """Busca y devuelve los detalles de la última evaluación de desempeño del empleado, incluyendo la calificación final y los criterios evaluados."""
    
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: 
        return "ERROR: No se encontró el registro de empleado."

    last_review_emp = EvaluacionEmpleado.objects.filter(empleado=empleado).order_by('-fecha_registro').first()

    if not last_review_emp:
        return "😔 Vaya, parece que no hay registros de evaluaciones de desempeño anteriores para mostrar."

    review_date_str = last_review_emp.fecha_registro.strftime("%d/%m/%Y")
    review_description = last_review_emp.evaluacion.descripcion or f"Evaluación {last_review_emp.evaluacion.id}"
    
    response_text = (
        f"📋 **Última Evaluación de Desempeño:** {review_description}\n"
        f"📅 **Fecha de Registro:** {review_date_str}\n"
    )
    
    criterios_calificados = EvaluacionEmpleadoCriterio.objects.filter(
        evaluacion_empleado=last_review_emp
    ).select_related('criterio')

    if criterios_calificados.exists():
        response_text += f"\n--- Desglose de Criterios ---\n"
        for calif_criterio in criterios_calificados:
            criterio_desc = calif_criterio.criterio.descripcion
            puntuacion = calif_criterio.calificacion_criterio
            response_text += f" • {criterio_desc}: **{puntuacion}**\n" 
    
    response_text += ( 
                      f"--------------------------------------\n"
                      f"⭐ **Calificación Final:** **{last_review_emp.calificacion_final or 'N/A'}**\n"
                      f"--------------------------------------"
    )
    if last_review_emp.comentarios and last_review_emp.comentarios.strip():
        response_text += f"\n\n💬 **Comentarios:** {last_review_emp.comentarios}\n"

    return response_text


@tool("get_current_contract_info", args_schema=GenericUserIDInput)
def get_current_contract_info_tool(user_id: int) -> str:
    """Busca y devuelve los detalles del contrato actual del empleado logueado."""
    
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: 
        return "ERROR: No se encontró el registro de empleado."

    current_contract = HistorialContrato.objects.filter(
        empleado=empleado,
        estado='activo'
    ).select_related('contrato', 'cargo').first() # Optimiza la consulta

    if not current_contract:
        current_contract = HistorialContrato.objects.filter(empleado=empleado).order_by('-fecha_inicio').first()
        if not current_contract:
             return "😔 Vaya, parece que no hay registros de contratos anteriores para mostrar."

    fecha_inicio_str = current_contract.fecha_inicio.strftime("%d/%m/%Y") if current_contract.fecha_inicio else "N/A"
    fecha_fin_str = current_contract.fecha_fin.strftime("%d/%m/%Y") if current_contract.fecha_fin else "Indefinida"
    
    response_text = (
        f"📄 **Detalles de tu Contrato Actual (o más reciente):**\n\n"
        f"🔧 **Cargo:** {current_contract.cargo.nombre if current_contract.cargo else 'N/A'}\n"
        f"📝 **Tipo de Contrato:** {current_contract.contrato.descripcion if current_contract.contrato else 'N/A'}\n"
        f"📊 **Estado:** {current_contract.get_estado_display()}\n\n"
        f"📅 **Inicio:** {fecha_inicio_str}\n"
        f"🔚 **Fin:** {fecha_fin_str}\n"
    )
    
    if current_contract.monto_extra_pactado:
         response_text += f"💰 **Sueldo Pactado (Extra):** ${current_contract.monto_extra_pactado}\n"

    if current_contract.condiciones and current_contract.condiciones.strip():
        response_text += f"\n💬 **Condiciones:** {current_contract.condiciones}\n"

    return response_text



@tool("get_internal_job_applications", args_schema=GenericUserIDInput)
def get_internal_job_applications_tool(user_id: int) -> str:
    """Busca y devuelve el estado de todas las solicitudes internas de trabajo (postulaciones a cargos) que el empleado ha realizado, ordenadas lógicamente por estado y fecha."""
    
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: 
        return "ERROR: No se encontró el registro de empleado."
        
    persona = empleado.persona_ptr 
    
    applications = Solicitud.objects.filter(
        persona=persona,
        es_interno=True,
        visible=True
    ).order_by('estado', '-fecha').select_related('cargo') 

    applications_list = list(applications)

    status_order = {'pendiente': 1, 'seleccionado': 2, 'descartado': 3}

    def sort_key(app):
        fecha_tuple = (app.fecha.year, app.fecha.month, app.fecha.day)
        return (status_order.get(app.estado, 99), -fecha_tuple[0], -fecha_tuple[1], -fecha_tuple[2])

    sorted_applications = sorted(applications_list, key=sort_key)

    if not sorted_applications:
        return "😔 Vaya, no has realizado ninguna postulación interna a cargos todavía."

    response_text = f"Aquí están todas tus postulaciones internas a cargos (ordenadas por estado y fecha):\n\n"
    
    for app in sorted_applications:
        fecha_str = app.fecha.strftime("%d/%m/%Y")
        estado_display = app.get_estado_display()
        
        response_text += (
            f"--- 💼 Postulación a {app.cargo.nombre} ---\n"
            f"📅 **Fecha:** {fecha_str}\n"
            f"📊 **Estado:** **{estado_display}**\n"
        )
        if app.descripcion and app.descripcion.strip():
             response_text += f"💬 **Notas:** {app.descripcion.strip()}\n"
        response_text += f"\n"

    return response_text




@tool("get_attendance_summary", args_schema=GenericUserIDInput)
def get_attendance_summary_tool(user_id: int) -> str:
    """Proporciona un resumen de asistencias de los últimos 30 días, incluyendo días presentes, tardanzas y horas totales."""
    
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: 
        return "ERROR: No se encontró el registro de empleado."

    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    attendances = HistorialAsistencia.objects.filter(
        empleado=empleado,
        fecha_asistencia__range=[start_date, end_date]
    ).order_by('fecha_asistencia')

    if not attendances.exists():
        return f"😔 No se encontraron registros de asistencia para el período del {start_date.strftime('%d/%m')} al {end_date.strftime('%d/%m')}."

    total_present_days = 0
    tardiness_days = 0
    total_seconds_worked = 0
    
    for record in attendances:
        if record.hora_entrada and record.hora_salida:
            total_present_days += 1
            
            datetime_entrada = datetime.combine(record.fecha_asistencia, record.hora_entrada)
            datetime_salida = datetime.combine(record.fecha_asistencia, record.hora_salida)
            
            duration = datetime_salida - datetime_entrada
            total_seconds_worked += duration.total_seconds()
            
            if record.tardanza:
                tardiness_days += 1

    hours = int(total_seconds_worked // 3600)
    minutes = int((total_seconds_worked % 3600) // 60)
    
    time_worked_display = f"{hours} horas, {minutes} minutos"
    total_absent_days = 30 - total_present_days

    response_text = (
        f"📊 **Resumen de Asistencia (Últimos 30 días):**\n\n"
        f"🗓️ **Período:** {start_date.strftime('%d/%m')} a {end_date.strftime('%d/%m')}\n"
        f"✅ **Días Presentes:** {total_present_days} días\n"
        f"🕒 **Horas Totales Trabajadas:** {time_worked_display} horas\n"
        f"⏰ **Días con Tardanza:** {tardiness_days} días\n"
        f"❌ **Ausencias/Faltas:** {total_absent_days} días\n\n"
        f"Si tienes dudas o consultas sobre un día específico, contacta con RRHH."
    )

    return response_text




HR_TOOLS = [
    get_vacation_days_tool, 
    get_benefits_tool, 
    get_discounts_tool, 
    get_current_role_and_department_tool,
    get_employee_objectives_tool,
    get_last_payroll_tool,
    get_last_performance_review_tool,
    get_current_contract_info_tool,
    get_internal_job_applications_tool,
    get_attendance_summary_tool

]
