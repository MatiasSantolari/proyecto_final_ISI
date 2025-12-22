from datetime import date
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from django.db.models import Sum
from ...models import *
from pydantic import BaseModel, Field 


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



HR_TOOLS = [
    get_vacation_days_tool, 
    get_benefits_tool, 
    get_discounts_tool, 
    get_current_role_and_department_tool,
    get_employee_objectives_tool,

]
