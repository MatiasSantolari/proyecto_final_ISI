from datetime import date, timedelta, datetime
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from django.db.models import Sum, Q
from ...models import *
from langchain_core.runnables import RunnableConfig
from django.db.models import Sum
from datetime import date
from typing import Annotated
from langchain_core.tools.base import InjectedToolArg


class BlindedAgentInput(BaseModel):
    """
    Oculta los identificadores del contexto del LLM.
    Impide que un atacante inyecte IDs falsos para espiar legajos ajenos.
    """
    pass


@tool("get_vacation_days", args_schema=BlindedAgentInput)
def get_vacation_days_tool(config: RunnableConfig) -> str: 
    """Calcula y devuelve los días de vacaciones disponibles, usados y pendientes del empleado logueado."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    total_disponibles = empleado.cantidad_dias_disponibles or 0
    usados = (VacacionesSolicitud.objects.filter(empleado=empleado, estado='aprobado', fecha_fin__lt=date.today()).aggregate(total=Sum('cant_dias_solicitados'))['total'] or 0)
    pendientes = (VacacionesSolicitud.objects.filter(empleado=empleado, estado__in=['pendiente', 'aprobado'], fecha_inicio__gte=date.today()).aggregate(total=Sum('cant_dias_solicitados'))['total'] or 0)
    disponibles = max(total_disponibles - usados - pendientes, 0)
    
    return (
        f"dias_disponibles_para_solicitar: {disponibles}, "
        f"total_anual_asignado: {total_disponibles}, "
        f"dias_usados_historicos: {usados}, "
        f"dias_pendientes_o_programados: {pendientes}"
    )


@tool("get_benefits", args_schema=BlindedAgentInput)
def get_benefits_tool(config: RunnableConfig) -> str:
    """Busca y lista los beneficios actuales del empleado logueado."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    beneficios = BeneficioEmpleadoNomina.objects.filter(empleado=empleado).select_related('beneficio').order_by('-id')[:10]
    if not beneficios.exists(): 
        return "info: el_empleado_no_tiene_beneficios_asignados"

    lista_benef = []
    for b in beneficios:
        valor = f"${b.beneficio.monto}" if b.beneficio.monto else (f"{b.beneficio.porcentaje}%" if b.beneficio.porcentaje else "activo")
        lista_benef.append(f"[{b.beneficio.descripcion}: {valor}]")
        
    return "beneficios_actuales: " + " , ".join(lista_benef)


@tool("get_discounts", args_schema=BlindedAgentInput)
def get_discounts_tool(config: RunnableConfig) -> str:
    """Busca y lista los descuentos/retenciones recientes del empleado logueado."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    descuentos = DescuentoEmpleadoNomina.objects.filter(empleado=empleado).select_related('descuento').order_by('-id')[:10]
    if not descuentos.exists(): 
        return "info: sin_descuentos_o_retenciones_registradas"
        
    lista_desc = []
    for d in descuentos:
        valor = f"${d.descuento.monto}" if d.descuento.monto else (f"{d.descuento.porcentaje}%" if d.descuento.porcentaje else "aplicado")
        lista_desc.append(f"[{d.descuento.descripcion}: {valor}]")
        
    return "descuentos_recientes: " + " , ".join(lista_desc)


@tool("get_current_role_and_department", args_schema=BlindedAgentInput)
def get_current_role_and_department_tool(config: RunnableConfig) -> str:
    """Obtiene el cargo y departamento actual del empleado logueado."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    cargo_actual = EmpleadoCargo.objects.filter(empleado=empleado, fecha_fin__isnull=True).select_related('cargo').first()
    if not cargo_actual:
        return "info: sin_cargo_o_departamento_activo_en_sistema"
        
    relacion = CargoDepartamento.objects.filter(cargo=cargo_actual.cargo).select_related('departamento').first()
    depto = relacion.departamento.nombre if relacion else "No asignado"
    
    return f"cargo_actual: {cargo_actual.cargo.nombre}, departamento: {depto}"


@tool("get_employee_objectives", args_schema=BlindedAgentInput)
def get_employee_objectives_tool(config: RunnableConfig) -> str:
    """Busca y lista los objetivos actuales y completados del empleado logueado."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    objetivos_activos = ObjetivoEmpleado.objects.filter(empleado=empleado, completado=False).select_related('objetivo').order_by('fecha_limite')
    objetivos_completados = ObjetivoEmpleado.objects.filter(empleado=empleado, completado=True).select_related('objetivo').order_by('-fecha_asignacion')[:5]

    if not objetivos_activos.exists() and not objetivos_completados.exists():
        return "info: el_empleado_no_tiene_objetivos_asignados"

    activos_list = [f"[{oe.objetivo.titulo} (Limite: {oe.fecha_limite.strftime('%d/%m/%Y') if oe.fecha_limite else 'Sin limite'})]" for oe in objetivos_activos]
    completados_list = [f"[{oe.objetivo.titulo}]" for oe in objetivos_completados]

    return f"objetivos_activos: {', '.join(activos_list) or 'Ninguno'}, objetivos_completados_recientes: {', '.join(completados_list) or 'Ninguno'}"


@tool("get_last_payroll", args_schema=BlindedAgentInput)
def get_last_payroll_tool(config: RunnableConfig) -> str:
    """Busca y devuelve los detalles de la última nómina (recibo de sueldo) del empleado logueado, incluyendo montos netos, brutos, beneficios y descuentos."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    last_payroll = Nomina.objects.filter(empleado=empleado).order_by('-id').first()
    if not last_payroll:
        return "info: sin_registros_de_nominas_anteriores"

    f_pago = last_payroll.fecha_pago.strftime("%d/%m/%Y") if last_payroll.fecha_pago else "N/A"
    
    return (
        f"periodo_numero: {last_payroll.numero or 'N/A'}, fecha_pago: {f_pago}, "
        f"monto_bruto: {last_payroll.monto_bruto}, total_beneficios: {last_payroll.total_beneficios}, "
        f"total_descuentos: {last_payroll.total_descuentos}, monto_neto_a_cobrar: {last_payroll.monto_neto}"
    )


@tool("get_last_performance_review", args_schema=BlindedAgentInput)
def get_last_performance_review_tool(config: RunnableConfig) -> str:
    """Busca y devuelve los detalles de la última evaluación de desempeño del empleado logueado, incluyendo la calificación final y los criterios evaluados."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    last_review_emp = EvaluacionEmpleado.objects.filter(empleado=empleado).select_related('evaluacion').order_by('-id').first()
    if not last_review_emp:
        return "info: sin_evaluaciones_de_desempeno_registradas"

    review_date = last_review_emp.fecha_registro.strftime("%d/%m/%Y")
    review_desc = last_review_emp.evaluacion.descripcion or f"Evaluacion {last_review_emp.evaluacion.id}"
    
    criterios_text = "Ninguno"
    criterios_calificados = EvaluacionEmpleadoCriterio.objects.filter(evaluacion_empleado=last_review_emp).select_related('criterio')
    if criterios_calificados.exists():
        criterios_text = " | ".join([f"{c.criterio.descripcion}: {c.calificacion_criterio}" for c in criterios_calificados])

    return (
        f"evaluacion: {review_desc}, fecha_registro: {review_date}, "
        f"calificacion_final: {last_review_emp.calificacion_final or 'N/A'}, "
        f"desglose_criterios: [{criterios_text}], comentarios_adicionales: {last_review_emp.comentarios or 'Ninguno'}"
    )


@tool("get_current_contract_info", args_schema=BlindedAgentInput)
def get_current_contract_info_tool(config: RunnableConfig) -> str:
    """Busca y devuelve los detalles del contrato actual del empleado logueado."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    current_contract = HistorialContrato.objects.filter(empleado=empleado, estado='active').select_related('contrato', 'cargo').first()
    if not current_contract:
        current_contract = HistorialContrato.objects.filter(empleado=empleado).select_related('contrato', 'cargo').order_by('-fecha_inicio').first()
        if not current_contract:
             return "info: sin_registros_de_contratos"

    f_inicio = current_contract.fecha_inicio.strftime("%d/%m/%Y") if current_contract.fecha_inicio else "N/A"
    f_fin = current_contract.fecha_fin.strftime("%d/%m/%Y") if current_contract.fecha_fin else "Indefinida"
    
    return (
        f"cargo: {current_contract.cargo.nombre if current_contract.cargo else 'N/A'}, "
        f"tipo_contrato: {current_contract.contrato.descripcion if current_contract.contrato else 'N/A'}, "
        f"estado_contrato: {current_contract.get_estado_display()}, fecha_inicio: {f_inicio}, fecha_fin: {f_fin}, "
        f"sueldo_extra_pactado: {current_contract.monto_extra_pactado or 0}, condiciones: {current_contract.condiciones or 'Ninguna'}"
    )


@tool("get_internal_job_applications", args_schema=BlindedAgentInput)
def get_internal_job_applications_tool(config: RunnableConfig) -> str:
    """Busca y devuelve el estado de todas las solicitudes internas de trabajo (postulaciones a cargos) que el empleado logueado ha realizado."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"
        
    applications = Solicitud.objects.filter(persona=empleado.persona_ptr, es_interno=True, visible=True).select_related('cargo').order_by('-fecha')
    if not applications.exists():
        return "info: el_empleado_no_tiene_postulaciones_internas"

    apps_list = []
    for app in applications:
        apps_list.append(
            f"[Cargo: {app.cargo.nombre}, Fecha: {app.fecha.strftime('%d/%m/%Y')}, "
            f"Estado: {app.get_estado_display()}, Notas: {app.descripcion or 'Ninguna'}]"
        )
    
    return "postulaciones_encontradas: " + " ; ".join(apps_list)


@tool("get_attendance_summary", args_schema=BlindedAgentInput)
def get_attendance_summary_tool(config: RunnableConfig) -> str:
    """Proporciona un resumen numérico de asistencias de los últimos 30 días del empleado logueado, incluyendo días presentes, tardanzas y horas totales."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    attendances = HistorialAsistencia.objects.filter(empleado=empleado, fecha_asistencia__range=[start_date, end_date])

    if not attendances.exists():
        return f"info: sin_registros_de_asistencia_desde_{start_date.strftime('%d/%m')}_al_{end_date.strftime('%d/%m')}"

    total_present_days = 0
    tardiness_days = 0
    total_seconds_worked = 0
    
    for record in attendances:
        if record.hora_entrada and record.hora_salida:
            total_present_days += 1
            dt_entrada = datetime.combine(record.fecha_asistencia, record.hora_entrada)
            dt_salida = datetime.combine(record.fecha_asistencia, record.hora_salida)
            total_seconds_worked += (dt_salida - dt_entrada).total_seconds()
            if record.tardanza:
                tardiness_days += 1

    hours = int(total_seconds_worked // 3600)
    minutes = int((total_seconds_worked % 3600) // 60)
    total_absent_days = max(30 - total_present_days, 0)

    return (
        f"rango_periodo: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}, "
        f"dias_presente: {total_present_days}, horas_totales_trabajadas: {hours}h {minutes}m, "
        f"dias_con_tardanza: {tardiness_days}, ausencias_o_faltas: {total_absent_days}"
    )



@tool("get_recommended_courses", args_schema=BlindedAgentInput)
def get_recommended_courses_tool(config: RunnableConfig) -> str:
    """Analiza el cargo actual del empleado logueado y devuelve los cursos de la cartelera disponibles para recomendación de la IA."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    cargo_actual = EmpleadoCargo.objects.filter(empleado=empleado, fecha_fin__isnull=True).select_related('cargo').first()
    if not cargo_actual:
        return "error: sin_cargo_activo_para_personalizar_recomendacion"

    relacion = CargoDepartamento.objects.filter(cargo=cargo_actual.cargo).select_related('departamento').first()
    depto_nombre = relacion.departamento.nombre if relacion else "General"
    cargo_nombre = cargo_actual.cargo.nombre

    inscripciones_ids = CapacitacionEmpleado.objects.filter(empleado=empleado).values_list('capacitacion_id', flat=True)
    
    cursos_disponibles = Capacitacion.objects.filter(activo=True).exclude(id__in=inscripciones_ids)

    if not cursos_disponibles.exists():
        return "info: sin_cursos_nuevos_disponibles_en_cartelera"

    lista_texto = ""
    for c in cursos_disponibles:
        tipo = "Externo" if c.es_externo else "Interno"
        lista_texto += f"- [{tipo}] {c.nombre}: {c.descripcion[:120]}...\n"

    return (
        f"perfil_empleado: [Cargo: '{cargo_nombre}', Departamento: '{depto_nombre}']. "
        f"cursos_disponibles_en_cartelera:\n{lista_texto}\n"
        f"INSTRUCCION: Selecciona los 2 o 3 cursos mas afines a su perfil y explica por qué le servirán."
    )


@tool("get_boss_and_manager_info", args_schema=BlindedAgentInput)
def get_boss_and_manager_info_tool(config: RunnableConfig) -> str:
    """Obtiene el nombre y mail del Jefe y del Gerente del departamento del usuario logueado."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    cargo_actual = EmpleadoCargo.objects.filter(empleado=empleado, fecha_fin__isnull=True).select_related('cargo').first()
    if not cargo_actual: return "error: sin_cargo_o_departamento_activo"

    relacion = CargoDepartamento.objects.filter(cargo=cargo_actual.cargo).select_related('departamento').first()
    if not relacion: return "error: sin_departamento_asociado_al_cargo"
    depto_obj = relacion.departamento

    jefe_emp = Empleado.objects.filter(
        empleadocargo__cargo__cargodepartamento__departamento=depto_obj,
        empleadocargo__cargo__es_jefe=True, 
        empleadocargo__fecha_fin__isnull=True
    ).select_related('persona_ptr').first()

    gerente_emp = Empleado.objects.filter(
        empleadocargo__cargo__cargodepartamento__departamento=depto_obj,
        empleadocargo__cargo__es_gerente=True,
        empleadocargo__fecha_fin__isnull=True
    ).select_related('persona_ptr').first()

    if jefe_emp:
        jefe_mail = jefe_emp.email if jefe_emp.email else "N/D"
        jefe_info = f"{jefe_emp.nombre} {jefe_emp.apellido} (Email: {jefe_mail})"
    else:
        jefe_info = "No asignado"

    if gerente_emp:
        gerente_mail = gerente_emp.email if gerente_emp.email else "N/D"
        gerente_info = f"{gerente_emp.nombre} {gerente_emp.apellido} (Email: {gerente_mail})"
    else:
        gerente_info = "No asignado"

    return f"departamento: {depto_obj.nombre}, jefe_directo: {jefe_info}, gerente_area: {gerente_info}"


@tool("get_team_members", args_schema=BlindedAgentInput)
def get_team_members_tool(config: RunnableConfig) -> str:
    """Obtiene la lista de compañeros de equipo (mismo departamento) y sus correos del usuario logueado."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    cargo_actual = EmpleadoCargo.objects.filter(empleado=empleado, fecha_fin__isnull=True).select_related('cargo').first()
    if not cargo_actual: return "error: sin_cargo_activo_en_sistema"

    relacion = CargoDepartamento.objects.filter(cargo=cargo_actual.cargo).select_related('departamento').first()
    if not relacion: return "error: sin_departamento_asignado"
    depto_obj = relacion.departamento

    companeros = Empleado.objects.filter(
        empleadocargo__cargo__cargodepartamento__departamento=depto_obj,
        empleadocargo__fecha_fin__isnull=True
    ).exclude(id=empleado.id).distinct().select_related('persona_ptr')

    if not companeros.exists():
        return f"departamento: {depto_obj.nombre}, estado: unico_integrante_activo"

    lista_comp = []
    for c in companeros:
        mail_texto = c.email if c.email else "Sin registro"
        lista_comp.append(f"[{c.nombre} {c.apellido} (Email: {mail_texto})]")
        
    return f"departamento: {depto_obj.nombre}, compañeros_de_equipo: " + " , ".join(lista_comp)


@tool("get_available_jobs_and_referrals", args_schema=BlindedAgentInput)
def get_available_jobs_and_referrals_tool(config: RunnableConfig) -> str:
    """Busca y devuelve los cargos y puestos de la empresa que tienen vacantes activas y visibles para postulación interna."""
    puestos_vacantes = CargoDepartamento.objects.filter(visible=True, vacante__gt=0).select_related('cargo', 'departamento').order_by('-id')
    
    if not puestos_vacantes.exists():
        return "info: sin_busquedas_laborales_internas_activas_en_este_momento"
        
    jobs_list = []
    for p in puestos_vacantes:
        desc_puesto = p.cargo.descripcion if p.cargo.descripcion else "Sin descripción adicional"
        jobs_list.append(
            f"[Cargo: {p.cargo.nombre}, Departamento: {p.departamento.nombre}, Vacantes_Disponibles: {p.vacante}, Detalles: {desc_puesto}]"
        )
        
    return "oportunidades_y_vacantes_disponibles: " + " ; ".join(jobs_list)


@tool("get_employee_achievements", args_schema=BlindedAgentInput)
def get_employee_achievements_tool(config: RunnableConfig) -> str:
    """Obtiene los logros, medallas o reconocimientos asignados al empleado logueado y verifica si poseen beneficios corporativos cruzados."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"
    
    logros_emp = LogroEmpleado.objects.filter(empleado=empleado, completado=True).select_related('logro').order_by('-fecha_asignacion')
    
    if not logros_emp.exists():
        return "info: el_empleado_no_registra_logros_o_premios_completados_todavia"
        
    achievements_list = []
    for le in logros_emp:
        logro_obj = le.logro
        fecha_logro = le.fecha_asignacion.strftime("%d/%m/%Y") if le.fecha_asignacion else "N/A"
        
        relacion_beneficio = LogroBeneficio.objects.filter(logro=logro_obj).select_related('beneficio').first()
        if relacion_beneficio and relacion_beneficio.beneficio:
            b = relacion_beneficio.beneficio
            valor_b = f"${b.monto}" if b.monto else (f"{b.porcentaje}%" if b.porcentaje else "Asignado")
            beneficio_info = f"Beneficio Otorgado: {b.descripcion} ({valor_b})"
        else:
            beneficio_info = "Reconocimiento de Mérito"
            
        activo_tag = "" if logro_obj.activo else " (Inactivo Global)"
            
        achievements_list.append(
            f"[Logro: {logro_obj.get_tipo_display()}{activo_tag} - Descripción: {logro_obj.descripcion}, Fecha_Obtencion: {fecha_logro}, {beneficio_info}]"
        )
        
    return "logros_y_medallas_del_colaborador: " + " ; ".join(achievements_list)


###########

class RequestVacationInput(BaseModel):
    """Esquema de entrada para registrar solicitudes de vacaciones."""
    fecha_inicio: str = Field(description="La fecha de inicio de las vacaciones en formato YYYY-MM-DD.")
    fecha_fin: str = Field(description="La fecha de fin de las vacaciones en formato YYYY-MM-DD.")

class ApplyToJobInput(BaseModel):
    """Esquema de entrada para registrar postulaciones internas."""
    puesto_nombre: str = Field(description="El nombre exacto o aproximado del cargo vacante al que se desea postular.")


@tool("get_salary_evolution", args_schema=BlindedAgentInput)
def get_salary_evolution_tool(config: RunnableConfig) -> str:
    """Obtiene el historial cronológico de actualizaciones salariales base ligadas al cargo actual del empleado."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"
    
    contrato_activo = HistorialContrato.objects.filter(empleado=empleado, estado='activo').select_related('cargo').first()
    if not contrato_activo or not contrato_activo.cargo:
        return "info: sin_contrato_o_cargo_activo_para_evaluar_sueldos"
    
    cargo_actual = contrato_activo.cargo
    historico_sueldos = HistorialSueldoBase.objects.filter(cargo=cargo_actual).order_by('fecha_sueldo')
    
    if not historico_sueldos.exists():
        return f"info: no_se_registran_actualizaciones_en_el_sueldo_base_para_el_cargo_{cargo_actual.nombre}"
        
    evolution_list = []
    for hs in historico_sueldos:
        fecha_cambio = hs.fecha_sueldo.strftime("%d/%m/%Y") if hs.fecha_sueldo else "N/A"
        evolution_list.append(f"[Fecha Entrada en Vigencia: {fecha_cambio}, Monto Sueldo Base: ${hs.sueldo_base}]")
        
    extra_pactado = f", Monto Extra Pactado en Contrato: ${contrato_activo.monto_extra_pactado}" if contrato_activo.monto_extra_pactado else ""
    
    return f"cargo_evaluado: {cargo_actual.nombre}{extra_pactado}, historico_de_escalas_salariales: " + " -> ".join(evolution_list)


@tool("request_vacation_days", args_schema=RequestVacationInput)
def request_vacation_days_tool(fecha_inicio: str, fecha_fin: str, config: RunnableConfig) -> str:
    """Registra una nueva solicitud de vacaciones en el sistema en estado pendiente para el empleado logueado."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    try:
        empleado = Empleado.objects.filter(usuario=user_id).first()
        if not empleado: return "error: empleado_no_encontrado"

        f_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        f_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

        if f_inicio > f_fin:
            return "error: fecha_inicio_posterior_a_fecha_fin"
        if f_inicio < date.today():
            return "error: fecha_inicio_en_el_pasado"

        dias_solicitados = (f_fin - f_inicio).days + 1

        total_disponibles = empleado.cantidad_dias_disponibles or 0
        usados = (VacacionesSolicitud.objects.filter(empleado=empleado, estado='aprobado', fecha_fin__lt=date.today()).aggregate(total=Sum('cant_dias_solicitados'))['total'] or 0)
        pendientes = (VacacionesSolicitud.objects.filter(empleado=empleado, estado__in=['pendiente', 'aprobado'], fecha_inicio__gte=date.today()).aggregate(total=Sum('cant_dias_solicitados'))['total'] or 0)
        disponibles_actuales = max(total_disponibles - usados - pendientes, 0)

        if dias_solicitados > disponibles_actuales:
            return f"error: saldo_insuficiente (Solicitados: {dias_solicitados}, Disponibles: {disponibles_actuales})"

        nueva_solicitud = VacacionesSolicitud.objects.create(
            empleado=empleado,
            fecha_inicio=f_inicio,
            fecha_fin=f_fin,
            cant_dias_solicitados=dias_solicitados,
            estado='pendiente'
        )

        return f"exito: solicitud_creada_id_{nueva_solicitud.id}_por_{dias_solicitados}_dias"

    except ValueError:
        return "error: formato_de_fechas_invalido"
    except Exception as e:
        return f"error_interno: {str(e)}"



@tool("postulate_to_internal_job", args_schema=ApplyToJobInput)
def postulate_to_internal_job_tool(puesto_nombre: str, config: RunnableConfig) -> str:
    """Crea una postulación interna para el empleado autenticado hacia un cargo con vacantes activas en un departamento."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"
    
    persona_obj = empleado.persona_ptr

    relacion_vacante = CargoDepartamento.objects.filter(
        cargo__nombre__icontains=puesto_nombre,
        visible=True,
        vacante__gt=0
    ).select_related('cargo', 'departamento').first()

    if not relacion_vacante:
        return "error: puesto_no_disponible_o_sin_vacantes_activas"

    cargo_destino = relacion_vacante.cargo
    depto_destino = relacion_vacante.departamento

    ya_postulado = Solicitud.objects.filter(
        persona=persona_obj, 
        cargo=cargo_destino, 
        es_interno=True, 
        visible=True
    ).exists()
    
    if ya_postulado:
        return "error: el_empleado_ya_esta_postulado_a_este_cargo"

    nueva_postulacion = Solicitud.objects.create(
        persona=persona_obj,
        cargo=cargo_destino,
        es_interno=True,
        visible=True,
        estado='pendiente',
        descripcion=f"Postulación automática al departamento de {depto_destino.nombre} generada vía RRHH Bot."
    )

    return f"exito: postulacion_registrada_id_{nueva_postulacion.id}_para_cargo_{cargo_destino.nombre}"


@tool("get_training_status_and_obligations", args_schema=BlindedAgentInput)
def get_training_status_and_obligations_tool(config: RunnableConfig) -> str:
    """Busca el listado y estado de todas las capacitaciones y cursos en los que el empleado logueado está inscripto, cursa o completó."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"
    
    inscripciones = empleado.mis_capacitaciones.select_related('capacitacion', 'capacitacion__institucion').order_by('-fecha_inscripcion')
    
    if not inscripciones.exists():
        return "info: el_empleado_no_tiene_inscripciones_a_cursos_activas"
        
    cursos_list = []
    for ins in inscripciones:
        cap = ins.capacitacion
        inst_nombre = cap.institucion.nombre if cap.institucion else "Interna / Propia de la empresa"
        f_insc = ins.fecha_inscripcion.strftime("%d/%m/%Y") if ins.fecha_inscripcion else "N/A"
        f_compl = f", fecha_finalizado: {ins.fecha_completado.strftime('%d/%m/%Y')}" if ins.fecha_completado else ""
        
        cursos_list.append(
            f"[Curso: {cap.nombre}, Estado_Actual: {ins.get_estado_display()}, Dictado_Por: {inst_nombre}, Inscrito_El: {f_insc}{f_compl}]"
        )
        
    return "estado_de_capacitaciones_del_usuario: " + " ; ".join(cursos_list)



@tool("register_daily_attendance", args_schema=BlindedAgentInput)
def register_daily_attendance_tool(config: RunnableConfig) -> str:
    """Registra la marca en tiempo real de asistencia para el día de hoy del empleado logueado, creando la entrada o actualizando la salida."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"
    
    ahora_completos = datetime.now()
    hoy_date = ahora_completos.date()
    hora_time = ahora_completos.time()
    
    asistencia_hoy = HistorialAsistencia.objects.filter(empleado=empleado, fecha_asistencia=hoy_date).first()
    
    if not asistencia_hoy:
        nueva_entrada = HistorialAsistencia.objects.create(
            empleado=empleado,
            fecha_asistencia=hoy_date,
            hora_entrada=hora_time,
            confirmado=False,
            tardanza=False
        )
        return f"exito: marca_de_ENTRADA_registrada_a_las_{hora_time.strftime('%H:%M:%S')}"
    
    elif asistencia_hoy.hora_entrada and not asistencia_hoy.hora_salida:
        asistencia_hoy.hora_salida = hora_time
        asistencia_hoy.save()
        return f"exito: marca_de_SALIDA_registrada_a_las_{hora_time.strftime('%H:%M:%S')}"
        
    else:
        f_entrada = asistencia_hoy.hora_entrada.strftime('%H:%M')
        f_salida = asistencia_hoy.hora_salida.strftime('%H:%M')
        return f"info: jornada_completada_previamente (Entrada: {f_entrada}, Salida: {f_salida})"


@tool("get_employee_skills", args_schema=BlindedAgentInput)
def get_employee_skills_tool(config: RunnableConfig) -> str:
    """Busca y lista todas las habilidades y competencias técnicas asignadas al perfil del empleado logueado, incluyendo descripciones y fechas de asignación."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id", 0)

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: 
        return "error: empleado_no_encontrado"

    habilidades = HabilidadEmpleado.objects.filter(empleado=empleado).select_related('habilidad').order_by('-fecha_asignacion')
    
    if not habilidades.exists(): 
        return "info: el_empleado_no_tiene_habilidades_o_competencias_tecnicas_asignadas"
        
    lista_hab = []
    for h in habilidades:
        activo_tag = "" if h.habilidad.activo else " (Inactiva Global)"
        
        fecha_str = h.fecha_asignacion.strftime("%d/%m/%Y") if h.fecha_asignacion else "Sin fecha"
        desc = f" ({h.habilidad.descripcion})" if h.habilidad.descripcion else ""
        lista_hab.append(f"[{h.habilidad.nombre}{activo_tag}{desc}, Asignada_El: {fecha_str}]")
        
    return "habilidades_perfil_tecnico: " + " ; ".join(lista_hab)



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
    get_attendance_summary_tool,
    get_recommended_courses_tool,
    get_boss_and_manager_info_tool,
    get_team_members_tool,
    get_available_jobs_and_referrals_tool,
    get_employee_achievements_tool,
    get_salary_evolution_tool,   
    request_vacation_days_tool,
    postulate_to_internal_job_tool,
    get_training_status_and_obligations_tool,
    register_daily_attendance_tool,
    get_employee_skills_tool,
]



############################################################
##  TOOLS DE MANUALES ##
############################################################
MENSAJE_PROHIBIDO = "Lo siento, no posees los permisos necesarios para realizar o consultar ese procedimiento en el sistema."


@tool
def manual_modulo_autenticacion_y_navegacion(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas básicas de la plataforma, 
    tales como: cómo obtener sus credenciales, cómo recuperar o cambiar su contraseña, 
    cómo cerrar sesión, cómo activar el modo oscuro/claro, qué opciones hay en la barra superior, 
    cómo actualizar sus datos personales, cargar el CV, estudios, certificaciones o historial laboral en su perfil.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    manual = """
    --- MANUAL DE PROCEDIMIENTOS: CREDENCIALES, INICIO Y BARRA SUPERIOR ---
    
    1. OBTENCIÓN DE CREDENCIALES:
    No te registres manualmente (quedarías como Postulante sin accesos). RR.HH. te dará de alta y el sistema te enviará un correo con tus accesos. 
    - Usuario: nombre.apellido (ej: juan.perez).
    - Contraseña inicial: Tu número de DNI (sin puntos ni espacios).

    2. RECUPERACIÓN Y CAMBIO DE CONTRASEÑA:
    - Si la olvidaste: En la pantalla de ingreso, haz clic en "¿Olvidó su contraseña?", pon tu correo registrado y te llegará un enlace de restablecimiento.
    - Si estás adentro del sistema: En la barra superior, despliega el ícono de usuario, selecciona "Cambiar Contraseña", ingresa tu clave actual, la nueva y confírmala.

    3. NAVEGACIÓN Y CONFIGURACIÓN VISUAL (BARRA SUPERIOR):
    - Modo Oscuro/Claro: Haz clic en el ícono de la "luna" o el "sol" en la barra superior para cambiar la iluminación y reducir la fatiga visual.
    - Cerrar Sesión: Despliega el ícono de usuario en la barra superior y selecciona "Cierre de Sesión" para salir de forma segura.

    4. ACTUALIZAR "MI PERFIL" (DATOS, ESTUDIOS Y CV):
    Ve a la barra superior y presiona en "Mi Perfil". Verás tus datos organizados en tarjetas. Al final de cada una, tienes botones para editar:
    - Datos Personales: Modifica tu teléfono, domicilio, localidad y carga tu Currículum Vitae (CV).
    - Datos Académicos: Registra tu formación (institución, título, fechas de inicio/fin y estado: en curso, finalizado o abandonado).
    - Certificaciones: Carga tus cursos y certificados detallando la institución, nombre del curso, fechas y estado.
    - Información Laboral: Completa tu trayectoria profesional previa indicando la organización, el cargo y el periodo de tiempo.
    """

    if rol_actual in ["admin", "administrador", "jefe", "gerente"]:
        manual += """
    
    5. CAMBIO DE VISTA / ROL (EXCLUSIVO LÍDERES Y ADMINS):
    - Debido a tus permisos de gestión, la barra superior te permite alternar libremente entre tus vistas de "Empleado" (para tus trámites personales), "Jefe/Gerente" y tu vista de "Administrador".
        """
        
    return manual



@tool
def manual_admin_personas(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Personas,
    tales como: registrar o crear una nueva persona, cómo se adaptan los formularios según el tipo 
    de usuario (Empleado, Jefe, Administrador, Normal), cómo se envían las credenciales de acceso, 
    cómo buscar y filtrar personas, o qué hacen los botones de la tabla (Editar, Ver, Desactivar/Reactivar).
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: SUBMÓDULO PERSONAS ---
    
    1. REGISTRO DE NUEVA PERSONA:
    - Presiona el botón "+ Crear nueva persona" para abrir el formulario de alta.
    - Datos obligatorios: Nombre, Apellido, DNI, Fecha de nacimiento, Género, Email, Teléfono (con prefijo), País, Provincia, Ciudad, Calle y Número.
    - Adaptación por Tipo de Usuario:
      * Empleado: Habilita de forma obligatoria Departamento, Cargo, Banco y CBU.
      * Jefe o Gerente: Solo habilita el campo Departamento.
      * Administrador: Habilita los campos Banco y CBU.
      * Normal: No requiere ninguna de estas asignaciones adicionales.
    - Opciones de Guardado:
      * "Guardar": Solo registra el perfil básico en el padrón.
      * "Guardar y crear contrato": Vincula de inmediato el registro con el módulo de contratos.

    2. NOTIFICACIÓN Y CREDENCIALES:
    - Tras guardar, el sistema envía un correo automático al usuario con sus accesos.
    - Formato de acceso: Usuario (nombre.apellido) y Contraseña (número de DNI sin puntos ni espacios).

    3. BÚSQUEDA, FILTRADO Y TABLA DE GESTIÓN:
    - Herramientas superiores: Permiten segmentar la lista por DNI, Departamento asignado o Tipo de usuario.
    - Acciones de la Tabla:
      * Editar: Modifica los datos del formulario original.
      * Ver: Muestra la ficha técnica completa del usuario.
      * Desactivar / Reactivar: Cambia el estado de actividad de la persona. Al desactivar, el registro se resguarda de forma segura para proteger la base de datos sin eliminar la información. Al reactivar, vuelve a estar disponible al instante.
    """


@tool
def manual_admin_cargos(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Cargos,
    tales como: definir posiciones laborales, crear un nuevo cargo, asignar sueldos iniciales, 
    configurar cupos o vacantes por cargo, filtrar cargos por departamento o gestionar la tabla 
    de posiciones (Editar sueldos, Ver fichas técnicas, Desactivar/Reactivar puestos).
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: SUBMÓDULO CARGOS ---
    
    1. REGISTRO DE NUEVO CARGO:
    - Presiona el botón "+ Crear nuevo cargo" para desplegar el formulario.
    - Requisitos obligatorios: Selección del departamento correspondiente, Nombre del cargo, Descripción detallada de funciones, Monto salarial inicial asignado y Número total de cupos (vacantes) disponibles para la organización.

    2. BÚSQUEDA Y FILTRADO:
    - Dispones de un Filtro por Departamento al lado del botón de creación. Permite aislar y visualizar únicamente las posiciones que pertenecen a un área específica de la empresa.

    3. TABLA DE GESTIÓN DE CARGOS:
    - Muestra los datos de: Nombre del cargo, Descripción, Sueldo base, Departamento y Vacantes totales.
    - Acciones disponibles:
      * Editar: Permite modificar los datos técnicos, actualizar el sueldo base o modificar el cupo de vacantes.
      * Ver: Acceso directo a la ficha técnica completa del cargo configurado.
      * Desactivar / Reactivar: Modifica el estado de actividad del puesto sin borrarlo. Desactivar resguarda el registro en la base de datos; reactivar lo vuelve a habilitar de forma inmediata.
    """


@tool
def manual_admin_departamentos(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Departamentos,
    tales como: definir unidades funcionales de la empresa, crear un nuevo departamento o área (ej. RRHH, IT, Ventas), 
    asignar responsabilidades principales a un área, editar denominaciones oficiales o cambiar el estado de actividad.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: SUBMÓDULO DEPARTAMENTOS ---
    
    1. REGISTRO DE NUEVO DEPARTAMENTO:
    - Presiona el botón de creación para abrir un formulario simplificado.
    - Campos requeridos: Denominación oficial del área (ej: Recursos Humanos, Ventas, IT) y Detalle de las funciones principales o responsabilidades del departamento.

    2. TABLA DE GESTIÓN DE DEPARTAMENTOS:
    - Muestra el listado de áreas configuradas con su Nombre y Descripción de actividad.
    - Acciones disponibles:
      * Editar: Modifica la denominación oficial o actualiza la descripción de tareas del área.
      * Ver: Brinda una visualización técnica completa de los datos cargados.
      * Desactivar / Reactivar: Cambia el estado del departamento sin eliminarlo físicamente. Al desactivar, el área y sus registros vinculados quedan resguardados de forma segura; al reactivar, vuelve a estar operativa al instante.
    """


@tool
def manual_admin_instituciones(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Instituciones Educativas,
    tales como: registrar centros de formación o universidades con convenios, dar de alta una nueva institución, 
    gestionar datos de contacto académico (Email, Teléfono, Dirección) o controlar la tabla de entidades educativas.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: SUBMÓDULO INSTITUCIONES EDUCATIVAS ---
    
    1. REGISTRO DE NUEVA INSTITUCIÓN:
    - Presiona el botón de creación para habilitar el formulario de datos de contacto institucional.
    - Campos obligatorios: Nombre (Denominación oficial de la universidad/instituto), Dirección (Ubicación física de la sede o campus), Teléfono y Email de contacto administrativo o de formación.

    2. TABLA DE GESTIÓN DE INSTITUCIONES:
    - Muestra la lista de entidades indexadas con Nombre, Dirección, Teléfono y Correo electrónico corporativo.
    - Acciones disponibles:
      * Editar: Permite corregir o actualizar los canales de contacto y la denominación de la entidad.
      * Ver: Ofrece la visualización completa de la ficha técnica de la institución educativa.
      * Desactivar / Reactivar: Altera la disponibilidad de la institución en el sistema sin borrarla de la base de datos. Desactivar oculta la entidad resguardando sus datos históricos; reactivar restablece su vigencia de forma inmediata.
    """


@tool
def manual_admin_administrar_postulaciones(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Administrar Postulaciones,
    tales como: ver el historial de postulaciones de los candidatos, consultar el panel de búsquedas activas o cerradas,
    ver el CV o ficha técnica de un postulante, finalizar postulaciones para un cargo, limpiar registros de postulantes,
    o reabrir la búsqueda de una vacante cerrada.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: ADMINISTRAR POSTULACIONES ---
    
    1. HISTORIAL DE POSTULACIONES:
    - Presiona el botón "Ver historial de postulaciones" en la parte superior para desplegar el modal con todas las aplicaciones históricas.
    - Datos visibles: Departamento, Cargo, Apellido, Nombre, DNI, Fecha de aplicación y Estado (ej: Pendiente, Aceptado).
    - Botones de acción: "Ver CV" (abre el PDF adjunto) y "Ver datos" (abre la ficha completa del postulante).

    2. PANEL DE CONTROL DE BÚSQUEDAS:
    - Se divide en dos bloques jerárquicos por Departamento:
      * Cargos con Búsqueda Activa: Vacantes que reciben postulantes actualmente.
      * Cargos con Búsqueda Cerrada: Procesos de selección finalizados o pausados.
    - Despliegue: Al presionar la flecha lateral de cada Cargo, se visualiza el listado inferior de sus respectivos postulantes (Nombre, DNI, Fecha, Estado, CV y Datos).

    3. ACCIONES DE CIERRE, LIMPIEZA Y REAPERTURA:
    - En Búsquedas Activas (debajo del listado del cargo):
      * "Finalizar postulaciones para este cargo": Traslada la vacante a "Búsqueda Cerrada", inhabilitando nuevas aplicaciones.
      * "Limpiar postulaciones": Elimina de forma definitiva todos los registros de postulantes guardados para ese cargo específico.
    - En Búsquedas Cerradas (al desplegar el cargo):
      * "Reabrir búsqueda para este cargo": Habilita nuevamente la vacante y la traslada al bloque de búsquedas activas.
    """


@tool
def manual_admin_gestionar_solicitudes_cargo(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Gestionar Solicitudes de Cargo,
    tales como: revisar el monitor de solicitudes de personal emitidas por los departamentos, auditar requerimientos pendientes,
    conocer el detalle técnico de un pedido o usar el módulo de revisión para aprobar o rechazar la apertura de vacantes.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: GESTIONAR SOLICITUDES DE CARGO ---
    
    1. MONITOR DE SOLICITUDES:
    - Muestra una tabla cronológica con todos los pedidos de personal.
    - Cada fila contiene: Fecha de solicitud, Departamento de origen, nombre del Solicitante, Cargo, Cupos pedidos y el Estado (Pendiente, Aprobado o Rechazado).

    2. MÓDULO DE REVISIÓN DETALLADA:
    - Haz clic en el botón de acción "Revisar" en cualquier fila para abrir el modal exhaustivo de auditoría.
    - Información disponible para evaluación:
      * Encabezado: Nombre del cargo, solicitante y área de origen.
      * Tipo de Solicitud: Indica si es un Cargo Nuevo (creación en el organigrama) o un Aumento de Cupo (añadir vacantes a un cargo existente).
      * Requerimientos: Cantidad exacta de vacantes solicitadas y la Descripción Base de la posición.
      * Perfil del Puesto: Detalle redactado por el área con las competencias, formación y experiencia específica requeridas para el triaje.
    """



@tool
def manual_admin_administrar_nominas(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Administrar Nóminas,
    tales como: liquidación de haberes, regenerar nóminas pendientes, generar nóminas del periodo actual,
    confirmar masivamente el pago de nóminas, filtrar o auditar liquidaciones por departamento/mes/año,
    o eliminar registros de nóminas pendientes con errores.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: ADMINISTRAR NÓMINAS ---
    
    1. PANEL DE ACCIONES MASIVAS (Herramientas por lotes en la parte superior):
    - Regenerar Nóminas Pendientes: Sincroniza y actualiza montos/conceptos de todas las liquidaciones no pagadas con los datos actuales del sistema.
    - Generar Nóminas Periodo Actual: Crea automáticamente los registros de liquidación para los empleados que aún no tienen una nómina en el ciclo vigente.
    - Confirmar Nóminas: Cambia masivamente el estado de las liquidaciones seleccionadas de "Pendiente" a "Pagado", dando por cerrado el proceso administrativo de pago.
    * Nota: El número entre paréntesis indica la cantidad de registros que serán afectados por la acción.

    2. HERRAMIENTAS DE AUDITORÍA Y FILTRADO:
    - Selectores superiores: Permiten segmentar por Departamento, Mes y Año.
    - Botón Filtrar: Ejecuta la búsqueda y actualiza el Monitor inferior.

    3. MONITOR DE LIQUIDACIONES Y ACCIONES INDIVIDUALES:
    - La tabla muestra: Nombre, Departamento, Fecha de generación, Monto final a percibir y Situación de pago (Pendiente o Pagado).
    - Acciones por fila:
      * Ver: Consulta el desglose exhaustivo de los conceptos de la nómina.
      * Eliminar: Quita la liquidación del sistema (solo se recomienda si está en estado 'Pendiente' y contiene errores).
    """


@tool
def manual_admin_tipos_contrato(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Tipos de Contrato,
    tales como: definir modalidades contractuales (Plazo Fijo, Indeterminado, Pasantía), crear un nuevo 
    tipo de contrato, configurar la duración base en meses o gestionar la tabla de modalidades (Editar, Ver, Desactivar).
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: TIPOS DE CONTRATO ---
    
    1. REGISTRO DE NUEVO TIPO DE CONTRATO:
    - Presiona el botón "+ Crear nuevo tipo de contrato".
    - Campos requeridos: Nombre/denominación de la modalidad contractual y Duración (meses) estipulada para dicha modalidad (ej: 3, 6, 12 meses).

    2. TABLA DE GESTIÓN Y ACCIONES:
    - Muestra la Descripción y la Duración total en meses cargada originalmente.
    - Acciones disponibles:
      * Editar: Permite modificar la descripción o ajustar la duración en meses del tipo de contrato.
      * Ver: Acceso a la visualización técnica de los datos del registro.
      * Desactivar / Reactivar: Modifica el estado de actividad sin eliminar el registro. Desactivar lo resguarda de forma segura en la base de datos; reactivar lo vuelve a habilitar de inmediato.
    """


@tool
def manual_admin_contratos(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Contratos,
    tales como: formalizar un contrato nuevo para un empleado, configurar vigencias (fechas de inicio y fin),
    cargar montos extras o adicionales al sueldo base, revisar el historial completo de contratos, filtrar 
    contratos por departamento, renovar un contrato vencido o finalizar un vínculo laboral.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: CONTRATOS ---
    
    1. FORMALIZACIÓN DE NUEVO CONTRATO:
    - Presiona el botón "+ Crear contrato nuevo" para abrir el formulario.
    - Campos obligatorios:
      * Empleado: Selector para vincular a la persona previamente registrada en el sistema.
      * Tipo de Contrato: Desplegable con las modalidades predefinidas (ej: Pasantía, Plazo Fijo).
      * Vigencia: Selección exacta de Fecha de inicio y Fecha de fin de la prestación.
      * Condiciones: Campo de texto libre para detallar cláusulas o acuerdos específicos.
      * Monto Extra (Opcional): Permite cargar un adicional fijo en dinero que se sumará al Sueldo Base del cargo del empleado.

    2. HERRAMIENTAS DE CONSULTA, HISTORIAL Y MONITOR:
    - Filtro por Departamento: Segmenta la vista de los contratos vigentes por área.
    - Historial de Contratos: Botón superior que despliega el registro histórico completo (pasados y presentes) indicando: Empleado, Cargo, Tipo, Fechas, Monto extra y Estado (Activo, Renovado o Finalizado).
    - Tabla principal: Muestra los contratos en curso con Nombre, Cargo, Tipo, Fechas de vigencia y Estado.

    3. GESTIÓN DEL CICLO DE VIDA (ACCIONES POR FILA):
    - Ver/Editar: Permite consultar o modificar datos técnicos y condiciones contractuales.
    - Renovar Contrato: Extiende la relación laboral de forma automática. Al llegar a la fecha de fin, le asigna un nuevo periodo de tiempo basado exactamente en la duración del Tipo de Contrato original (ej: si era un contrato de 6 meses, la renovación otorga otros 6 meses adicionales automáticamente).
    - Finalizar Contrato: Da por concluido el vínculo de forma manual, cambiando el estado del registro a "Finalizado".
    """


@tool
def manual_admin_beneficios(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Beneficios,
    tales como: configurar un nuevo beneficio, incentivo o premio no remunerativo, establecer modalidades 
    de cálculo por monto fijo o porcentaje sobre el sueldo base, configurar la condición de permanencia 
    (beneficios fijos o de única vez), o administrar la tabla de conceptos activos.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: BENEFICIOS ---
    
    1. CONFIGURACIÓN DE NUEVO BENEFICIO:
    - Presiona el botón "+ Crear nuevo tipo de beneficio" para abrir el formulario.
    - Campos obligatorios: Nombre identificatorio del concepto (ej: Bono Presentismo, Adicional Título).
    - Modalidades de Cálculo (debes elegir una):
      * Monto: Se ingresa una cantidad fija de dinero.
      * Porcentaje: Se ingresa un valor numérico porcentual que el sistema calculará sobre el Sueldo Base del empleado al generar la nómina.
    - Condición de Permanencia (Check "Fijo"):
      * Si está marcado (Es Fijo): El beneficio queda asignado de forma permanente en cada periodo de liquidación posterior.
      * Si NO está marcado (No es Fijo): Es de carácter único; se aplica en la nómina del mes actual y el sistema lo remueve automáticamente para el siguiente periodo.

    2. TABLA DE GESTIÓN Y ACCIONES:
    - Muestra la descripción, columnas de Monto/Porcentaje, Estado (Activo) y si es Fijo (Sí/No).
    - Acciones: Editar (ajusta valores o permanencia), Ver (ficha técnica) y Desactivar/Reactivar (resguarda el registro en la base de datos sin eliminarlo).
    """


@tool
def manual_admin_descuentos(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Descuentos,
    tales como: configurar nuevas deducciones, retenciones o cargos específicos, establecer descuentos 
    por monto fijo o porcentaje sobre el sueldo base, configurar deducciones fijas o de única vez (como adelantos), 
    o gestionar la tabla de descuentos y retenciones de haberes.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: DESCUENTOS ---
    
    1. CONFIGURACIÓN DE NUEVO DESCUENTO:
    - Presiona el botón de creación para abrir el formulario de deducciones.
    - Campos obligatorios: Nombre de la deducción (ej: Adelanto de sueldo, Seguro adicional, Cuota sindical).
    - Modalidades de Cálculo (debes elegir una):
      * Monto: Cantidad fija de dinero a restar.
      * Porcentaje: Valor porcentual a calcular y deducir sobre el Sueldo Base del empleado.
    - Condición de Permanencia (Check "Fijo"):
      * Si está marcado (Es Fijo): El descuento se aplicará automáticamente en todos los meses/periodos posteriores.
      * Si NO está marcado (No es Fijo): Se aplica como una deducción por única vez en la nómina del ciclo vigente y el sistema lo desvincula automáticamente para el mes siguiente.

    2. TABLA DE GESTIÓN Y ACCIONES:
    - Presenta el listado de deducciones con su Descripción, Monto/Porcentaje, Estado y si es Fijo (Sí/No).
    - Acciones: 
      * Editar: Para actualizar valores o condiciones del descuento.
      * Ver: Consulta técnica del registro completo.
      * Desactivar / Reactivar: Permite modificar el estado de actividad de un registro sin eliminarlo del sistema. Al Desactivar, el registro se resguarda para proteger la base de datos. Al Reactivar, vuelve a estar disponible de inmediato.
    """



@tool
def manual_admin_asignador_beneficios_descuentos(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Asignador de Beneficios y Descuentos,
    tales como: vincular conceptos a los empleados, usar los filtros por departamento, realizar asignaciones individuales,
    realizar asignaciones masivas o en bloque mediante checks, o cómo consultar las asignaciones actuales de un colaborador.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN Y GESTIÓN: ASIGNADOR DE BENEFICIOS/DESCUENTOS ---
    
    1. PANEL DE SELECCIÓN Y FILTROS (Parte superior):
    - Filtro por Departamento: Permite segmentar la lista de empleados para aislar un área específica.
    - Selector de Beneficio: Menú desplegable para elegir el concepto premiador predefinido que se desea aplicar.
    - Selector de Descuentos: Menú desplegable para elegir la deducción predefinida que se desea aplicar.
    - Botón "Asignar a Seleccionados": Procesa y ejecuta la vinculación de los conceptos seleccionados para todos los empleados marcados.

    2. TABLA DE GESTIÓN DE PERSONAL Y CONSULTA:
    - Columnas disponibles: Selección (Check), Nombre, Apellido, DNI, Departamento y Cargo.
    - Columna "Asignaciones Actuales": Cuenta con un botón que despliega una ventana emergente (pop-up) con el listado de todos los beneficios y descuentos que ese empleado específico tiene vinculados en ese momento.

    3. METODOLOGÍAS DE OPERACIÓN (CÓMO ASIGNAR):
    - Camino A: Asignación Individual
      * Elige el beneficio o descuento en los selectores superiores.
      * Busca al empleado en la tabla y presiona el botón directo de la columna "Acciones" en su fila correspondiente.
    - Camino B: Asignación Masiva / En Bloque
      * Primero: Selecciona el beneficio, el descuento o ambos conceptos en los selectores superiores del panel.
      * Segundo: Marca las casillas de selección (checks) de todos los empleados a quienes deseas aplicarles dichos conceptos.
      * Tercero: Presiona el botón superior "Asignar a seleccionados" para consolidar la vinculación masiva en el sistema.
    """


@tool
def manual_admin_capacitaciones_y_cursos(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Capacitaciones y Cursos,
    tales como: registrar o crear una nueva formación (interna o externa), cargar imágenes publicitarias, 
    gestionar vigencias y cupos ilimitados, interactuar con el monitor de formación o dar de alta instituciones desde el formulario.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: CAPACITACIONES Y CURSOS ---
    
    1. REGISTRO DE NUEVA FORMACIÓN (El formulario cambia según el selector "Externo"):
    - A. Capacitación Interna (Propia de la empresa):
      * Requiere: Nombre, Descripción, Vigencia (Fecha inicio y fin) y Cupos (Vacantes disponibles).
      * Atajos: Si no tiene fechas fijas, marca "Sin fecha". Si no hay límite de asistentes, marca "Ilimitado".
      * Institución: Selección de entidad académica. Si no existe, presiona el botón "+" para darla de alta (Nombre, Dirección, Teléfono, Email) sin salir del formulario actual.
      * Imagen: Permite subir una imagen publicitaria para la cartelera pública.
      * Modalidad: Permite tildar si es "Presencial" y si es "Capacitación propia".
    - B. Curso Externo:
      * Requiere los mismos datos que la interna, pero añade obligatoriamente el campo "URL del curso".
      * Los campos de "Cupos" y "Capacitación propia" quedan inhabilitados en esta modalidad.

    2. MONITOR DE FORMACIÓN Y ACCIONES:
    - La tabla principal muestra: Detalles del Curso (Nombre e Institución), Categorización (Interno/Externo y Estado Activo/Inactivo) y Disponibilidad (Fecha inicio y Cupos).
    - Acciones: Editar/Ver (modificar datos técnicos o ficha) y Desactivar/Reactivar (quita el curso de la cartelera pública para resguardarlo sin borrarlo del sistema).
    """


@tool
def manual_admin_administrar_evaluaciones(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Administrar Evaluaciones,
    tales como: crear matrices de evaluación, ponderar criterios, gestionar el panel de control, duplicar evaluaciones,
    asignar o quitar empleados de una evaluación, o realizar y cargar el proceso de calificación.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN Y GESTIÓN: ADMINISTRAR EVALUACIONES ---
    
    1. CREACIÓN DE UNA NUEVA EVALUACIÓN (Asistente de configuración):
    - Paso 1: Ingresa la Descripción y la Fecha programada.
    - Paso 2 (Selección de Criterios): Elige un Tipo de Criterio del desplegable, marca los indicadores específicos y asígnales una Ponderación.
      * Regla Crítica: La suma de ponderaciones de un mismo tipo debe ser igual a 1. Si es menor, el sistema las nivelará automáticamente al pulsar "Agregar Criterios".
    - Panel de Selección (Derecha): Agrupa los criterios por tipo. Puedes borrarlos con la "X" lateral antes de presionar "Guardar Evaluación".

    2. PANEL DE CONTROL DE EVALUACIONES:
    - Muestra descripción, fecha, estado (Activa/Inactiva) y el desglose de pesos.
    - Acciones (Botón Ver / Tres puntos): Permite Editar estructura, Duplicar la evaluación (para reutilizar sus criterios) o Activar/Desactivar el registro.
    - Columna Empleados: Redirige a la sección de Gestión de Empleados (el botón dirá Ver o Editar según el estado).

    3. GESTIÓN Y ASIGNACIÓN DE EMPLEADOS:
    - Filtros: Permite segmentar por DNI o Departamento.
    - Columna Asignación (Tabla de Gestión):
      * Si no está asignado: Aparece el botón "Asignar" para vincularlo.
      * Si está asignado (y no calificado): Permite "Quitar la asignación".
      * Si ya está calificado: El botón se bloquea automáticamente para proteger la integridad del dato.

    4. PROCESO DE CALIFICACIÓN (Columna "Calificar"):
    - Editar (Cargar Calificación): Despliega los criterios. El evaluador ingresa la nota y el sistema calcula el puntaje Total automáticamente según los pesos. Requiere de forma obligatoria el campo "Comentario del Evaluador".
    - Ver (Detalle): Permite consultar la hoja de notas final terminada con observaciones del superior.
    """


@tool
def manual_admin_tipos_criterios(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Tipos de Criterios,
    tales como: definir categorías generales de evaluación (ej: Habilidades Blandas), usar la función 'Crear otro tipo' 
    para cargas masivas de categorías y gestionar la tabla de categorías (Editar, Ver, Desactivar).
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: TIPOS DE CRITERIOS ---
    
    1. CARGA ÁGIL DE TIPOS DE CRITERIO (Formulario dinámico optimizado):
    - Ingresa el nombre de la primera categoría general (ej: Competencias Técnicas).
    - Función "Crear otro tipo": Pulsa este botón para que el sistema genere automáticamente un nuevo campo de texto debajo del anterior.
    - Carga Masiva: Repite el proceso las veces que necesites. Al finalizar, presiona el botón de guardado para registrar todas las categorías de forma simultánea de un solo golpe.

    2. TABLA DE GESTIÓN DE CATEGORÍAS:
    - Muestra el listado de todos los tipos creados.
    - Acciones: Editar (corrige la denominación), Ver (visualización técnica) y Desactivar/Reactivar (resguarda el registro en la base de datos sin borrar el historial).
    """


@tool
def manual_admin_criterios_evaluacion(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Criterios de Evaluación,
    tales como: definir indicadores de medición específicos (ej: Trabajo en equipo), usar el formulario de carga grupal, 
    vincular indicadores a un tipo de criterio, o gestionar la tabla de criterios configurados.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: CRITERIOS DE EVALUACIÓN ---
    
    1. REGISTRO DE NUEVOS CRITERIOS (Carga Grupal en bloque):
    - Paso 1: En el menú desplegable "Tipo de Criterio", selecciona la categoría a la que pertenecerán (ej: Habilidades Blandas).
    - Paso 2: En "Descripción del Criterio", ingresa el nombre del indicador específico (ej: Trabajo en equipo).
    - Función "Crear otro criterio": Presiona este botón para generar un nuevo campo de descripción abajo. Esto permite cargar múltiples criterios para el mismo tipo seleccionado de una sola vez.
    - Finalización: Presiona el botón de guardado para registrar simultáneamente todos los indicadores en el sistema.

    2. TABLA DE GESTIÓN DE CRITERIOS:
    - Muestra la descripción detallada de cada indicador y el tipo de criterio al que está vinculado.
    - Acciones: Editar (modifica la descripción o reasigna la categoría), Ver (visualización técnica) y Desactivar/Reactivar (resguarda el registro en la base de datos sin eliminarlo).
    """


@tool
def manual_admin_gestor_objetivos(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Gestor de Objetivos,
    tales como: crear o definir metas y tareas, configurar objetivos diarios recurrentes, establecer plazos límite,
    asignar objetivos a un empleado específico o mediante una plantilla por cargo, o interactuar con el panel de control.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN Y GESTIÓN: GESTOR DE OBJETIVOS ---
    
    1. CREACIÓN DE OBJETIVOS:
    - Presiona el botón "+ Nuevo Objetivo" en la parte superior para abrir el formulario.
    - Campos obligatorios: Nombre del objetivo y detalle de la tarea a realizar.
    - Check "Objetivo diario/recurrente": Si se activa, el sistema generará la tarea automáticamente cada día y bloqueará el campo de Fecha de vencimiento.
    - Plazo límite: Selección de fecha de vencimiento (solo disponible si NO es recurrente).
    - Opciones de finalización:
      * "Guardar": Almacena la meta en la base de datos para su uso posterior.
      * "Guardar y Asignar": Registra el objetivo y abre automáticamente el módulo de asignación.

    2. METODOLOGÍAS DE ASIGNACIÓN (Modalidades de vinculación):
    - Camino A (Empleado específico): Selecciona el Departamento, marca individualmente a los empleados de la lista en pantalla y presiona "Confirmar asignación".
    - Camino B (Plantilla por cargo): Permite la asignación masiva a un puesto entero. Selecciona el Departamento, elige el Cargo específico y presiona "Confirmar asignación".

    3. PANEL DE CONTROL Y ACCIONES DE LA TABLA:
    - Muestra: Título, Descripción, Recurrencia (Único o Diario), fechas (Creación/Vencimiento) y Estado (Activo/Inactivo).
    - Acciones disponibles por fila:
      * Ver/Editar: Consulta detalles o modifica la información técnica de la meta.
      * Asignar: Acceso directo al modal de asignación (individual o por cargo).
      * Habilitar/Deshabilitar: Alterna el estado del objetivo para pausarlo sin eliminarlo.
    """


@tool
def manual_admin_logros(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Logros y Gamificación,
    tales como: configurar un nuevo logro o reconocimiento, entender los tipos de logro por sistema, vincular 
    beneficios e incentivos asociados, crear un beneficio rápido desde el formulario, o gestionar la tabla de logros.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: LOGROS (GAMIFICACIÓN Y RECONOCIMIENTOS) ---
    
    1. CONFIGURACIÓN DE NUEVO LOGRO:
    - Presiona el botón "+ Crear nuevo logro" para desplegar el formulario.
    - Campos obligatorios: Nombre o detalle del hito a alcanzar (ej: "Empleado del Mes", "Cero Inasistencias").
    - Tipo de Logro (Sistema): Menú desplegable con opciones predefinidas.
      * Nota técnica: Estos tipos están integrados en el código debido a que dependen de una lógica de programación automática (ej: cálculo automático de puntualidad). El administrador solo puede elegir de la lista existente.
    - Beneficio Asociado: Selector para elegir qué premio creado previamente se otorgará automáticamente al colaborador que obtenga el logro.
    - Atajo de Creación Rápida: Si el premio deseado no existe en la lista, el botón "+" junto al selector abre un modal para registrar un nuevo beneficio (Monto/Porcentaje, Fijo o no) sin abandonar la carga actual del logro.

    2. TABLA DE GESTIÓN Y ACCIONES:
    - Muestra la descripción, el tipo de obtención por sistema y el incentivo vinculado (Monto exacto o Porcentaje sobre sueldo).
    - Acciones disponibles:
      * Editar: Modifica la descripción o cambia el beneficio/premio asignado.
      * Ver: Ofrece la visualización técnica completa del registro del logro.
      * Desactivar / Reactivar: Altera el estado del reconocimiento sin borrarlo. Desactivar resguarda el registro en la base de datos; reactivar lo vuelve a habilitar de inmediato.
    """


@tool
def manual_admin_habilidades(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Habilidades,
    tales como: registrar nuevas competencias técnicas o blandas (ej. Python, Liderazgo), detallar las capacidades 
    específicas que comprende una habilidad, o interactuar con la tabla de gestión de competencias del repositorio.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE ADMINISTRACIÓN: REPOSITORIO DE HABILIDADES ---
    
    1. REGISTRO DE NUEVA HABILIDAD:
    - Presiona el botón "+ Crear nueva habilidad" para abrir el formulario simplificado.
    - Campos requeridos: Denominación de la competencia (ej: "Liderazgo de Equipos", "Python Avanzado", "Resolución de Conflictos") y Detalle de las capacidades, conocimientos o aptitudes específicas que comprende dicha habilidad.

    2. TABLA DE GESTIÓN DE COMPETENCIAS:
    - Presenta el listado completo de las habilidades configuradas en el sistema con su Nombre y Descripción técnica.
    - Acciones disponibles:
      * Editar: Permite actualizar el nombre o profundizar/corregir la descripción de capacidades.
      * Ver: Brinda una visualización técnica completa de todos los datos cargados.
      * Desactivar / Reactivar: Cambia el estado de actividad del registro sin eliminarlo físicamente. Al desactivar, la habilidad queda resguardada de forma segura en la base de datos; al reactivar, vuelve a estar disponible para el armado de perfiles de inmediato.
    """


@tool
def manual_operaciones_confirmar_asistencia(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Confirmar Asistencia,
    tales como: supervisar o validar la jornada laboral del personal, confirmar asistencias de hoy, 
    marcar tardanzas a los empleados, registrar ausentes de forma masiva o interactuar con la tabla de registros diarios.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE OPERACIONES: CONFIRMAR ASISTENCIA ---
    
    1. BOTONES DE ACCIÓN RÁPIDA (Parte superior):
    - Confirmar Asistencia: Valida formalmente el registro de jornada de los empleados que hayan sido seleccionados en la tabla.
    - Marcar Tardanza: Registra un ingreso fuera de horario para los colaboradores seleccionados.
    - Registrar Ausentes de Hoy (Acción Masiva): No requiere selección previa. Al presionarlo, el sistema identifica de forma automática a todo el personal que no haya realizado ninguna marca de ingreso en el día y los registra como "Ausente".

    2. TABLA DE REGISTROS DIARIOS:
    - Muestra al personal que interactuó con el sistema en la fecha actual, detallando: Nombre, Departamento, Cargo, Hora de entrada, Hora de salida y columnas indicadoras de "Confirmado" y "Tardanza".

    3. PROCEDIMIENTO PASO A PASO PARA VALIDAR PRESENTISMO:
    - Paso 1 (Selección): Busca al empleado en la tabla y marca el cuadro de verificación (check) ubicado al final de su fila. Puedes marcar varios empleados simultáneamente para trabajar en lote.
    - Paso 2 (Ejecución): Presiona el botón superior "Confirmar Asistencia" para validar sus horas o "Marcar Tardanza" si ingresaron tarde.
    - Paso 3 (Cierre de jornada): Una vez finalizada la ventana de ingreso permitida de la empresa, pulsa el botón "Registrar Ausentes de hoy" para completar el reporte diario de todo el equipo automáticamente.
    """


@tool
def manual_operaciones_gestionar_vacaciones(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Gestionar Vacaciones,
    tales como: revisar, validar o desestimar solicitudes de descanso anual, consultar el cómputo o saldo 
    de días de vacaciones de un empleado, o cómo funcionan los botones de aceptar y rechazar licencias pendientes.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE OPERACIONES: GESTIONAR VACACIONES ---
    
    1. MONITOR CENTRAL DE SOLICITUDES:
    - Presenta una tabla con el historial de pedidos de licencia de los empleados.
    - Información técnica visible por fila: Nombre completo, Departamento, Fecha exacta de inicio y finalización del pedido, Cómputo de días (cuántos días abarca el pedido), Saldo actual (días que el empleado tiene a favor antes de esta solicitud) y Estado (Pendiente, Rechazado o Aceptado).

    2. PROCESAMIENTO DE SOLICITUDES PENDIENTES (Última columna de la tabla):
    - Botón Aceptar: Aprueba la licencia del colaborador. Al presionarlo, el sistema realiza dos acciones automáticas: descuenta los días correspondientes del saldo del empleado y cambia el estado del trámite a "Aceptado".
    - Botón Rechazar: Desestima el pedido de descanso. El estado del trámite cambia a "Rechazado" y los días a favor del colaborador se mantienen intactos, sin sufrir ningún descuento.
    """


@tool
def manual_autogestion_mis_asistencias(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en su panel personal de Asistencia,
    tales como: ver el detalle de marcas diarias de entrada o salida, consultar el historial de jornadas pasadas,
    verificar si su jefe confirmó su presentismo o comprobar si tiene marcas registradas como tardanzas.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual == "normal":
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE AUTOGESTIÓN: REGISTRO DE ASISTENCIA ---
    
    1. MÓDULO DEL DÍA (Panel Superior):
    - Muestra la fecha actual y el estado en tiempo real de tu registro diario.
    - Aquí puedes visualizar tus horarios exactos de entrada y salida (una vez grabados) junto con el botón correspondiente para registrar tu marca de ingreso o egreso laboral.

    2. HISTORIAL DE ASISTENCIAS (Panel Inferior):
    - Presenta una tabla cronológica con el registro histórico de tus jornadas trabajadas.
    - Datos visibles: Fecha, horas exactas de entrada/salida, marca visual de "Confirmación" (validada por tu superior) y el "Estado" de la jornada (A tiempo, Pendiente o Tardanza).
    """


@tool
def manual_autogestion_mis_nominas(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en su panel personal de Nóminas,
    tales como: consultar el historial de recibos de sueldo o liquidaciones de haberes, ver las fechas de pago,
    conocer los montos netos percibidos o revisar el desglose económico de ingresos, beneficios y descuentos.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual == "normal":
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE AUTOGESTIÓN: MIS NÓMINAS (RECIBOS DE SUELDO) ---
    
    1. TABLA PRINCIPAL DE LIQUIDACIONES:
    - Permite consultar el historial completo de tus haberes devengados.
    - Información directa por fila: Período correspondiente (mes/año), fecha de pago efectiva, monto final percibido y el estado administrativo del recibo (Pagado o Pendiente).

    2. MÓDULO DE REVISIÓN DETALLADA (Al pulsar el botón "Ver"):
    - Accedes al desglose exhaustivo de la nómina seleccionada, organizado en:
      * Datos del Empleado: Tu nombre completo, DNI, cargo ocupado y departamento.
      * Información del Comprobante: Número de nómina correlativo, fecha de generación, fecha de pago y estado actual.
      * Desglose Económico: Listado pormenorizado de tus Ingresos Brutos, Beneficios asignados (con sus totales) y el detalle de los Descuentos o retenciones aplicadas.
      * Monto Neto: El valor final líquido a percibir en mano tras procesar todas las deducciones.
    """


@tool
def manual_autogestion_mis_contratos(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en su panel de Contratos Personales,
    tales como: consultar las condiciones de su relación contractual, verificar vigencias o fechas de inicio/fin,
    revisar el sueldo base y montos extras pactados, o leer las cláusulas técnicas asentadas por la empresa.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual == "normal":
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE AUTOGESTIÓN: MIS CONTRATOS ---
    
    1. TABLA PRINCIPAL DE CONTRATOS:
    - Muestra de forma directa el historial y estado de tu relación contractual con la empresa.
    - Datos visibles: Cargo ocupado, tipo de contrato, fecha de inicio, fecha de finalización pactada, monto extra asignado y el estado del vínculo (Activo, Renovado o Finalizado).

    2. DETALLE EXHAUSTIVO DEL ACUERDO (Al pulsar el botón "Ver"):
    - Despliega la ficha legal y económica del contrato vigente o histórico:
      * Información del Puesto: Cargo desempeñado, departamento de asignación y tipo de modalidad contractual (ej: Plazo Fijo, Pasantía, Indeterminado).
      * Vigencia del Vínculo: Fechas exactas de inicio de la prestación y de finalización prevista en el acuerdo.
      * Condiciones Económicas: Desglose del sueldo base asociado a la posición y el detalle del monto extra o adicionales fijos pactados de forma opcional.
      * Cláusulas y Acuerdos: Espacio técnico detallado donde se especifican las condiciones generales, responsabilidades específicas y observaciones asentadas por la administración.
    """


@tool
def manual_autogestion_mis_vacaciones(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en su panel personal de Vacaciones,
    tales como: consultar su saldo de días disponibles, realizar una nueva solicitud de descanso anual,
    revisar el estado de sus pedidos (Aprobada, Pendiente, Rechazada) o cómo cancelar un pedido pendiente.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual == "normal":
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE AUTOGESTIÓN: MIS VACACIONES ---
    
    1. CONTROL DE SALDOS Y NUEVAS SOLICITUDES (Panel Superior):
    - Visualizarás de forma destacada tu saldo de días de vacaciones disponibles a favor.
    - Procedimiento para pedir vacaciones: Selecciona la fecha de inicio y la fecha de fin en los selectores del panel y presiona el botón para generar la solicitud. El trámite pasará a revisión de tus superiores.

    2. HISTORIAL DE PEDIDOS Y CONTROL (Tabla Inferior):
    - Registra todas tus solicitudes históricas, detallando: fechas de inicio/fin, cantidad de días laborales netos y el estado actual del trámite (Pendiente, Aprobada, Rechazada o Cancelada).
    - Anulación de pedidos: Si deseas cancelar una solicitud que hiciste por error, busca la fila en la tabla inferior y, siempre que se encuentre en estado "Pendiente", utiliza el botón de cancelación disponible allí mismo.
    """


@tool
def manual_autogestion_cursos_capacitaciones(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en la Cartelera de Formación interna,
    tales como: explorar e inscribirse a cursos y capacitaciones, diferenciar cursos internos de externos,
    usar el buscador por palabras clave, filtrar por categoría o tipo, o ingresar a los detalles con 'Ver más'.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual == "normal":
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE AUTOGESTIÓN: CARTELERA DE FORMACIÓN Y CURSOS ---
    
    1. HERRAMIENTAS DE BÚSQUEDA Y FILTRADO (Parte Superior):
    - Buscador libre: Escribe palabras clave del curso que buscas (ej: "Excel", "Liderazgo").
    - Selectores de Filtro: Permiten segmentar por Categoría o por Tipo de dictado:
      * Internos: Capacitaciones dictadas de forma directa por la propia empresa.
      * Externos: Cursos académicos ofrecidos por instituciones aliadas con convenios.

    2. EXPLORACIÓN DE LA OFERTA ACADÉMICA:
    - Cada publicación de la cartelera contiene: Imagen y Título, Modalidad (presencial, virtual o híbrida), Fecha Límite máxima para mostrar interés e inscribirse, y una Descripción o resumen breve de contenidos.
    - Si deseas profundizar en el temario, haz clic en el botón "Ver más" de la tarjeta del curso.

    3. PROCEDIMIENTO DE INSCRIPCIÓN (Varía según el tipo de curso):
    - Para Cursos Internos: Tienen cupos limitados y fecha de cierre estricta. Para asegurar tu vacante, debes ingresar a la publicación y pulsar obligatoriamente el botón “Inscribirme”.
    - Para Cursos Externos: No requieren preinscripción en nuestro sistema. Encontrarás en la misma publicación el botón "Ver Información Externa", el cual te redirigirá automáticamente al sitio web de la institución aliada para gestionar tu cursada.
    """


@tool
def manual_autogestion_ofertas_empleo(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER para postularse a búsquedas internas,
    tales como: acceder a ofertas de empleo abiertas, verificar o actualizar el Currículum Vitae (CV) 
    en formato PDF antes de aplicar, explorar las vacantes por cargo o ejecutar la postulación en el sistema.
    """
    return """
    --- MANUAL DE AUTOGESTIÓN: OFERTAS DE EMPLEO Y BÚSQUEDAS INTERNAS ---
    
    1. PASO 1: ACCESO A LAS OFERTAS
    - Dirígete al menú lateral izquierdo de la plataforma y selecciona la opción "Ofertas de Empleo".

    2. PASO 2: CONTROL Y ACTUALIZACIÓN DEL CURRÍCULUM (CV)
    - Al ingresar, el sistema evaluará tu perfil y te lanzará una alerta: "¿Tu CV está actualizado?". 
    - Como política de la empresa, es vital que tu formación y datos recientes estén cargados antes de aplicar. Si necesitas corregir algo, haz clic en el botón "Actualizar" para ingresar y cargar tu Currículum Vitae en formato PDF.

    3. PASO 3: EXPLORAR VACANTES DISPOSIBLES
    - En la pantalla se desplegará el listado de búsquedas abiertas en el organigrama. Cada tarjeta te mostrará de forma transparente: Nombre del cargo vacante, Descripción detallada de las tareas y responsabilidades asociadas, y el Departamento al que pertenece la posición.

    4. PASO 4: EJECUTAR LA POSTULACIÓN
    - Localiza la oferta laboral que se alinee con tu perfil profesional.
    - Presiona el botón directo "Postularme".
    - Confirmación del Sistema: Una vez que hagas clic, el botón se ocultará automáticamente para evitar duplicados y verás en su lugar una etiqueta de color verde con el texto "Postulado", acompañada por la fecha exacta del día en que aplicaste.
    """


@tool
def manual_autogestion_solicitar_personal(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte CÓMO HACER tareas en el submódulo de Solicitar Nuevo Personal,
    tales como: formalizar el pedido de nuevas vacantes ante RRHH, crear una nueva solicitud de personal, 
    pedir aumento de cupos para cargos existentes, dar de alta un nuevo cargo en el organigrama, 
    detallar el perfil y requisitos solicitados, o revisar el historial de pedidos de su departamento.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DE AUTOGESTIÓN: SOLICITAR NUEVO PERSONAL ---
    
    1. CREACIÓN DE UNA NUEVA SOLICITUD DE VACANTE:
    - Presiona el botón "+ Crear Nueva Solicitud" en la parte superior para desplegar el modal de configuración de parámetros.
    - Configuración del Tipo de Cargo (Dispones de dos caminos en el selector):
      * Opción A ("Cupos cargos existentes"): Elige esta modalidad si necesitas reforzar un equipo actual incorporando más personal a un puesto que ya funciona en la empresa. Luego, selecciona el puesto específico en el desplegable "Seleccione el cargo actual".
      * Opción B ("Crear nuevo cargo"): Utiliza esta alternativa si la posición que buscas incorporar no existe todavía en el organigrama de la empresa. El sistema habilitará campos de texto para que ingreses el Nombre y la Descripción de las nuevas funciones operativas.
    - Cantidad de Cupos: Ingresa numéricamente el total de vacantes netas que deseas cubrir con esta solicitud.
    - Perfil y Requisitos: Redacta en el espacio detallado las competencias clave, formación académica mínima y experiencia específica que se buscan para cubrir la posición solicitada.
    - Finalización: Presiona el botón "Enviar solicitud" para que el pedido sea derivado automáticamente al departamento de Recursos Humanos para su correspondiente revisión.

    2. TABLA DE HISTORIAL Y SEGUIMIENTO DE PEDIDOS:
    - Debajo del botón verás el listado histórico de requerimientos emitidos exclusivamente por tu departamento.
    - Información de control por fila: Fecha de creación, nombre del Líder Solicitante, Tipo de solicitud (Cargo nuevo o Aumento de cupo), Nombre del Cargo, Cantidad de cupos pedida y el Estado del Trámite (Aprobada, Rechazada o Pendiente de revisión por la administración).
    - Botón de Acción "Ver": Permite ingresar a consultar el formulario técnico completo junto con todos los comentarios históricos que la administración haya asociado a la solicitud.
    """


@tool
def manual_dashboard_general_ia(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte sobre la pantalla principal del Dashboard, 
    cómo descargar el PDF del panel, cómo funciona el Reporte con IA, qué contiene el informe escrito 
    por inteligencia artificial (Diagnóstico, Alertas, Sugerencias) o cómo ver el Historial de Reportes.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DEL DASHBOARD: CONTROL GENERAL E INFORMES CON IA ---
    
    1. PANTALLA PRINCIPAL:
    - Es el panel de control central de la organización donde se visualiza el estado general de la empresa mediante indicadores de alto nivel y gráficas de tendencia.

    2. HERRAMIENTAS DE IA Y REPORTES (Ícono de "estrellas" en el extremo derecho superior):
    - Al presionarlo, despliega tres opciones clave: Descargar en formato PDF, Analizar y Generar Reporte con IA, y Ver Historial de Reportes Generados.
    - Funcionamiento de la IA: Cruza automáticamente los datos de todos los módulos del sistema (asistencias, nóminas, evaluaciones, objetivos, etc.) y entrega un informe de gestión estructurado en tres bloques clave:
      * A. Diagnóstico del Negocio: Resumen rápido del total de empleados activos, gasto total en sueldos ($) y el promedio general de notas de desempeño de la empresa.
      * B. Alertas con Nombre y Apellido: Detecta desvíos críticos (Rojo) y alertas de rendimiento (Amarillo). Ejemplos: quiénes faltaron más en los últimos 30 días, qué área sufre más ausentismo, qué empleados desaprobaron evaluaciones (nota menor a 6) o si hay acumulado de vacaciones sin aprobar y proyectos trabados en 0%.
      * C. Sugerencias y Planes de Acción: Recomendaciones operativas concretas para solucionar el ausentismo, qué cursos específicos asignarle a los colaboradores con notas bajas para que mejoren, y cómo destrabar las metas demoradas.
    """


@tool
def manual_dashboard_detalle_empleados(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte sobre las tarjetas de KPIs del Dashboard, 
    el acceso al detalle de Empleados Activos, cómo descargar el CSV de personal, cómo filtrar la nómina, 
    o qué información contienen los paneles e historial de la Ficha Personal de un empleado.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DEL DASHBOARD: ACCESOS DIRECTOS Y DETALLE DE EMPLEADOS ---
    
    1. TARJETAS DE INDICADORES CLAVE (KPIs SUPERIORES):
    - Son cuatro rectángulos presionables que funcionan como accesos directos a sus historiales: Empleados Activos, Ausencias del Mes, Costo Laboral y Promedio de Evaluaciones.

    2. MONITOR DETALLADO DE EMPLEADOS ACTIVOS (Al pulsar su KPI correspondiente):
    - Filtros disponibles: Búsqueda por DNI, por Departamento y por Estado (Activo, Inactivo, Licencia, Suspendido, En Prueba, Jubilado).
    - Descarga de datos: El botón "CSV" (arriba a la derecha) descarga la información de la pantalla. Si aplicas filtros, el archivo solo contendrá esos datos segmentados.
    - Vista general: Muestra Nombre, DNI, Estado, Departamento, Cargo, Fecha de Ingreso y Días de Vacaciones Disponibles.

    3. FICHA PERSONAL DEL COLABORADOR (Al hacer clic sobre el Nombre del empleado):
    - Panel Izquierdo: Muestra Foto, nombre, cargo, DNI, fecha de ingreso, estado y saldo de vacaciones.
    - Panel Derecho (Estructurado en Pestañas de Historial):
      * Historial de Cargos: Registra los puestos ocupados, departamentos y fechas de inicio/fin.
      * Historial de Nóminas: Detalla fechas, neto final y montos específicos de beneficios/descuentos (Pagado/Pendiente).
      * Evaluaciones: Lista las fechas, descripción, calificaciones obtenidas y botón "Ver/Calificar".
      * Asistencia: Muestra el calendario de fechas, horarios registrados, confirmación de líderes y tardanzas.
      * Vacaciones: Detalla todas las solicitudes, periodos, días corridos/hábiles y estado (Pendiente, Aceptado, Rechazado o Cancelado).
      * Objetivos: Permite filtrar por tipo (Empleado/Cargo) y detalla la meta, asignación, límite y si fue completado.
    """


@tool
def manual_dashboard_detalle_asistencias(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte sobre el detalle del KPI de Ausencias, 
    el monitor de puntualidad del Dashboard, cómo filtrar las asistencias de los empleados 
    o cómo descargar el reporte CSV de presentismo diario.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DEL DASHBOARD: MONITOR DE PUNTUALIDAD Y AUSENCIAS ---
    
    1. ACCESO AL MONITOR DE PUNTUALIDAD:
    - Se ingresa presionando sobre el KPI rectangular de "Ausencias del Mes" en el Dashboard.

    2. HERRAMIENTAS DE SEGMENTACIÓN Y DESCARGA:
    - Filtros: Permite buscar por DNI, aislar por Departamento, filtrar por registros Confirmados (Sí/No) y por marcas con Tardanza (Sí/No).
    - Descarga: Cuenta con un botón para exportar la grilla de datos actual directamente a un archivo CSV.

    3. VISUALIZACIÓN DE DATOS DE LA TABLA:
    - Muestra de forma cronológica: Nombre Completo del colaborador (funciona como link directo para abrir su perfil), número de DNI, Departamento asignado, Fecha de asistencia evaluada, Hora de entrada, Hora de salida, y las etiquetas de estado de Confirmación y Tardanza.
    """


@tool
def manual_dashboard_detalle_costos(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte sobre el detalle del KPI de Costo Laboral, 
    el control financiero del Dashboard, cómo filtrar nóminas liquidadas, el uso del botón 'Pagar Ahora' 
    o la descarga del CSV económico de personal.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DEL DASHBOARD: CONTROL FINANCIERO Y COSTOS LABORALES ---
    
    1. ACCESO AL CONTROL DE COSTOS:
    - Se ingresa haciendo clic sobre el KPI rectangular de "Costo Laboral" en el panel superior.

    2. FILTRADO Y EXPORTACIÓN DE HABERES:
    - Filtros superiores: Segmentación rápida por número de DNI, Estado de la Nómina (Pagado/Pendiente) y por Departamento de origen.
    - Exportación: Incluye un botón para descargar en formato CSV la planilla financiera visualizada.

    3. TABLA DE LIQUIDACIÓN Y GESTIÓN DE PAGO:
    - Datos generales: Nombre del empleado (con enlace a su ficha), DNI, Departamento, Cargo y la Fecha de generación del recibo.
    - Bloque de Cierre Económico: Muestra de forma transparente el total acumulado de beneficios, el total de descuentos aplicados y el valor Neto final a transferir.
    - Estado de Pago: Indica la fecha exacta en la que se efectuó el pago. En caso de registros en estado "Pendiente", el sistema habilita el botón interactivo "Pagar Ahora" para procesar la transacción individual en ese momento.
    """


@tool
def manual_dashboard_detalle_evaluaciones(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte sobre el detalle del KPI de Promedio de Evaluaciones, 
    el monitor de calificaciones del Dashboard, cómo filtrar las notas de desempeño de los empleados 
    o el uso del botón 'Sin Calificar'.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DEL DASHBOARD: MONITOR DE CALIFICACIONES Y DESEMPEÑO ---
    
    1. ACCESO AL MONITOR DE RENDIMIENTO:
    - Se ingresa haciendo clic sobre el KPI rectangular de "Promedio de Evaluaciones" en el panel de control.

    2. HERRAMIENTAS DE AUDITORÍA:
    - Filtros superiores: Permiten aislar registros mediante el DNI del empleado o buscando por el Tipo/Descripción específica de la evaluación (ej: "Evaluación de blandas 1"). Incluye un botón para descargar las notas en CSV.

    3. VISUALIZACIÓN DE NOTAS Y ACCIONES DE CARGA:
    - Estructura de la grilla: Detalla el nombre del empleado (con acceso a su perfil), DNI, tipo de evaluación ejecutada y la fecha exacta del registro.
    - Control de Calificación: Muestra de forma directa el puntaje numérico final obtenido por el colaborador. 
    - Atajo de Calificación: Si el empleado fue asignado pero aún no cuenta con una nota cargada, el sistema mostrará el botón interactivo "Sin Calificar". Al presionarlo, redirigirá al líder directamente a la interfaz operativa para registrar la calificación y comentarios del evaluador de forma inmediata.
    """


@tool
def manual_dashboard_graficos_vacaciones(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte sobre la tarjeta de analítica de Vacaciones del Dashboard, 
    el Gráfico de Torta o Donut de licencias, cómo cambiar los meses de visualización del gráfico 
    o cómo gestionar solicitudes pendientes (Aceptar/Rechazar) desde la redirección del Dashboard.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DEL DASHBOARD: GRÁFICOS Y ACCESO DIRECTO A VACACIONES ---
    
    1. ANALÍTICA VISUAL (TARJETA DE VACACIONES EN EL DASHBOARD):
    - Rango temporal: En la parte superior de la tarjeta se indica el rango de fechas exactas ("Desde - Hasta") que abarca la información.
    - Selector de meses: Dispone de un menú desplegable interactivo para elegir cuántos meses hacia atrás deseas analizar en la gráfica (ej: últimos 3 meses, 6 meses, etc.).
    - Gráfico de Torta (Donut): Muestra de manera porcentual la distribución de los descansos del personal mediante porciones de colores: Aprobadas, Pendientes, Rechazadas y Canceladas. En el hueco central del gráfico se visualiza el Número Total neto de solicitudes acumuladas de todas las porciones combinadas.

    2. REDIRECCIÓN A LA INTERFAZ DE ADMINISTRACIÓN DETALLADA:
    - Al hacer clic directamente sobre el título "Vacaciones" de la tarjeta, el sistema te redirigirá a una pantalla de administración avanzada.
    - Tabla de Supervisión de Registros: Permite auditar el Nombre, departamento, Fecha de inicio, fecha de fin, Cantidad de días solicitados netos y la columna crítica de "Días Disponibles" (saldo a favor del empleado al momento de la consulta).
    - Botones de Gestión (Última columna): Muestra las opciones operativas "Aceptar" o "Rechazar" únicamente en aquellas filas cuyo estado sea "Pendiente". 
    * Nota de Seguridad: Para resguardar el historial legal y evitar modificaciones accidentales, una vez que el registro fue procesado (Aceptado o Rechazado), los botones de acción desaparecen automáticamente de la interfaz.
    """


@tool
def manual_dashboard_graficos_asistencia(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte sobre la tarjeta de analítica de Asistencias y Tardanzas, 
    el Gráfico de Barras verticales segmentadas (Presentes, Tardanzas, Ausentes), cómo usar las etiquetas flotantes 
    del gráfico o cómo funciona la redirección al Detalle de Asistencias nominales.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DEL DASHBOARD: GRÁFICOS DE ASISTENCIA Y TARDANZAS ---
    
    1. GRÁFICO DE BARRAS VERTICALES DE ASISTENCIA:
    - Rango temporal: En la parte superior indica el rango de fechas que el gráfico está analizando. Cuenta con una sección para ajustar el periodo de visualización y profundidad del análisis.
    - Segmentación por columnas: Cada barra vertical se divide en tres colores:
      * Cantidad de Presentes: Empleados que marcaron asistencia en tiempo y forma.
      * Cantidad de Tardanzas: Empleados que ingresaron fuera del horario estipulado.
      * Cantidad de Ausentes: Personal sin ninguna marca de asistencia en la jornada.
    - Etiqueta flotante: Al colocar el cursor sobre cualquier segmento de color, se despliega una ventana flotante con la cantidad numérica exacta y la fecha de ese registro.

    2. REDIRECCIÓN AL DETALLE NOMINAL:
    - Al presionar sobre el título de la tarjeta "Asistencia / Tardanza", el sistema te redirige automáticamente a la sección de Detalle de Asistencias (Submódulo 4.3). Allí podrás aplicar filtros por DNI o Departamento y descargar el reporte en formato CSV.
    """


@tool
def manual_dashboard_graficos_costos(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte sobre las tarjetas financieras del Dashboard, 
    tales como: el Gráfico Donut de Costos Desglosados, los porcentajes de impacto presupuestario, 
    la Gráfica de Líneas de Comparativa de Costo Laboral entre dos años, o las redirecciones a los paneles de pago.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DEL DASHBOARD: COSTOS DESGLOSADOS Y COMPARATIVA ANUAL ---
    
    1. TARJETA NÓMINA: COSTOS DESGLOSADOS (Gráfico Donut / Torta):
    - Estructura: Analiza la composición financiera de los pagos indicando el rango de tiempo (ajustable mediante un menú desplegable).
    - Centro del gráfico: Muestra la cifra neta del Costo Total sumado de todos los ítems.
    - Referencias (Derecha): Detalla por concepto (Sueldo Básico, Beneficios, Horas Extra) su nombre, el porcentaje (%) que representa sobre el gasto total y la cantidad numérica exacta en dinero.
    - Redirección: Al presionar sobre el título de la tarjeta, te redirige al Detalle de Costos y Nóminas (Submódulo 4.4) para filtrar y descargar el CSV.

    2. TARJETA COMPARATIVA DE COSTO LABORAL (Gráfico de Líneas):
    - Estructura: Análisis histórico de tipo anual por mes (Enero a Diciembre). Cuenta con un menú desplegable doble para seleccionar y comparar dos años específicos entre sí (ej: 2024 vs 2025).
    - Líneas de movimiento: Línea Azul (primer año seleccionado) y Línea Verde (segundo año seleccionado).
    - Interacción: Al colocar el cursor sobre cualquier punto del mes, una etiqueta flotante muestra el costo exacto de ambos años en ese periodo para detectar incrementos o ahorros. Presionar el título redirige al Detalle de Costos (Submódulo 4.4).
    """


@tool
def manual_dashboard_graficos_desempenio_y_estructura(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte sobre los gráficos estadísticos de rendimiento, 
    la Distribución de Calificaciones con degradado estilo semáforo, el Gráfico de Barras horizontales 
    de Empleados por Departamento, o cómo se actualiza la distribución del talento humano.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DEL DASHBOARD: DISTRIBUCIÓN DE CALIFICACIONES Y PERSONAL ---
    
    1. TARJETA DISTRIBUCIÓN DE CALIFICACIONES (Gráfico de Barras Verticales):
    - Estructura: Análisis cuantitativo de notas obtenidas (rango de fechas ajustable por menú desplegable).
    - Ejes: Horizontal (Indica la calificación del 1 al 10) y Vertical (Cantidad de evaluaciones con esa nota).
    - Degradado estilo Semáforo: Rojo (Calificaciones bajas/bajo rendimiento), Amarillo (Calificaciones medias) y Verde (Calificaciones altas/excelencia).
    - Redirección: Al presionar sobre el título, te traslada a la sección de Histórico de Evaluaciones (Submódulo 4.5) para filtrar por DNI o nombre de evaluación y bajar el CSV.

    2. TARJETA ESTRUCTURA: EMPLEADOS POR DEPARTAMENTO (Gráfico de Barras Horizontales):
    - Estructura: Radiografía rápida de la distribución del talento en la empresa.
    - Visualización: El eje izquierdo lista los Departamentos (IT, Ventas, etc.). La longitud de la barra horizontal indica de forma proporcional la cantidad de empleados asignados, mostrando el número neto exacto al final de la barra.
    - Sincronización: No requiere mantenimiento manual; el gráfico se actualiza automáticamente cada vez que se modifica el área de un empleado en su Perfil 360° (Submódulo 4.2) o se realizan movimientos en el módulo de Estructura.
    """


@tool
def manual_dashboard_graficos_objetivos_y_capacitaciones(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte sobre las analíticas de metas y formación del Dashboard, 
    tales como: la tarjeta de Progreso de Objetivos, el semáforo inteligente de avance, el gráfico de barras 
    de Impacto de Capacitaciones (Inscripciones Internas vs Interés Externo) o la interfaz de auditoría académica profunda.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual not in ["admin", "administrador", "jefe", "gerente"]:
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DEL DASHBOARD: SEGUIMIENTO DE METAS Y RENDIMIENTO ACADÉMICO ---
    
    1. TARJETA PROGRESO DE OBJETIVOS (Gráfico de Barras de Avance):
    - Estructura: Muestra el avance en tiempo real de las metas de los equipos. Cuenta con un menú desplegable para segmentar y consultar los objetivos por área específica (ej: "Ventas").
    - Indicadores por fila: Detalla Nombre/Descripción de la meta, Departamento asignado y Tipología (Único o Recurrente diario).
    - Barra de Progreso Semáforo: Muestra el porcentaje exacto calculado según los empleados que completaron la tarea frente al total. Cambia de color: Rojo (Progreso crítico/inicial), Amarillo (Intermedio/En proceso) y Verde (Cerca de completarse o Finalizado).
    - Origen: Se alimenta del módulo Gestor de Objetivos (3.3); cualquier actualización de un empleado impacta de inmediato.

    2. TARJETA IMPACTO DE CAPACITACIONES (Gráfico de Comparativa Visual):
    - Estructura: Ubicado en la base del Dashboard, mide el alcance de la formación indicando el rango de fechas (ajustable por menú desplegable temporal).
    - Barras adyacentes de origen: Barra de Inscripciones Internas (empleados anotados en cursos de la empresa) y Barra de Interés Externo (colaboradores que consultaron por cursos de instituciones aliadas).
    - Redirección y Auditoría Profunda (Al presionar el título de la tarjeta):
      * Filtros: Permite buscar por DNI, Nombre del curso, Origen (Interno/Externo) y Estado de inscripción (Interesado, Realizando, Finalizado, Abandonado). Posee botón para limpiar filtros y botón para exportar a CSV.
      * Tabla Académica: Muestra Nombre del empleado (con enlace a Perfil 360°), DNI, Nombre del curso, tipología y Estado exacto de avance del alumno.
    """


@tool
def manual_plataforma_chatbot_rrhh(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando el usuario pregunte sobre cómo funciona el ChatBot del sistema, 
    dónde encontrarlo, qué consultas puede resolver, qué temas analiza o cómo borrar el historial 
    de la conversación actual para reiniciar el chat con la IA.
    """
    return """
    --- MANUAL DE LA PLATAFORMA: ASISTENTE VIRTUAL (CHATBOT RRHH) ---
    
    1. ACCESO DIRECTO AL CHAT:
    - El asistente inteligente está disponible de forma permanente en cualquier pantalla del sistema, ubicado como un ícono de chat flotante en la esquina inferior derecha de la interfaz. Al presionarlo, se despliega la ventana interactiva.

    2. INTERFAZ Y COMANDOS DE CONTROL:
    - Encabezado: Se identifica visualmente con el título "ChatBot RRHH" en el margen superior de la ventana.
    - Reiniciar Conversación: Junto al título se encuentra el ícono de una papelera. Al presionarlo, puedes borrar de forma definitiva el historial de la conversación actual y reiniciar el chat desde cero con la IA de forma segura.

    3. CAPACIDADES Y ALCANCE DE CONSULTAS (INTERACCIÓN EN LENGUAJE NATURAL):
    - Puedes escribirle preguntas libres sobre tu situación particular o procesos de la empresa. El asistente está capacitado para analizar el contexto y resolver dudas exactas sobre:
      * Beneficios: Consulta de montos, tipos y conceptos percibidos en tu legajo.
      * Vacaciones: Información de saldos de días disponibles y estados de solicitudes.
      * Evaluaciones: Resúmenes de calificaciones obtenidas y comentarios de desempeño de tus superiores.
      * Objetivos: Seguimiento de metas asignadas pendientes y control de fechas límite.
      * Información General: Respuestas directas a dudas frecuentes sobre políticas y procedimientos internos.
    """



@tool
def manual_dashboard_empleado_tareas_y_objetivos(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando un empleado pregunte sobre su pantalla de inicio, cómo completar 
    sus tareas diarias, qué significa el estado visual muteado, cómo ver los objetivos de su puesto, 
    cómo usar los filtros de tareas (Recurrentes/Únicas) o qué información hay en la planilla de seguimiento.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual == "normal":
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DEL DASHBOARD EMPLEADO: TAREAS DIARIAS Y OBJETIVOS ---
    
    1. PANEL DE TAREAS DIARIAS (Pantalla de inicio):
    - Muestra una barra de progreso que se completa a medida que marcas tus pendientes del día.
    - Acción: Al marcar el check de una tarea, pasa a "Completada" y cambia su estado visual a un tono atenuado (muteado).
    - Redirección: Al presionar sobre el título “Tareas Diarias”, el sistema te lleva al historial detallado.

    2. HISTORIAL Y PLANILLA DE SEGUIMIENTO DE TAREAS:
    - Filtros superiores: Permiten segmentar entre "Tareas Recurrentes" (rutina diaria automática) y "Tareas Únicas" (proyectos aislados con fecha única).
    - Grilla de auditoría (ordenada de más reciente a antigua): Detalla Título, Descripción, Fecha Límite, Tipo (recurrente/aislada) y Estado mediante tres etiquetas:
      * Pendiente: Sin acciones realizadas todavía.
      * No Completado: El plazo de entrega venció sin que hayas marcado el check.
      * Completado: Marcada exitosamente en tiempo y forma.

    3. PANEL DE OBJETIVOS DE MI PUESTO:
    - Muestra una barra de avance y el listado de metas específicas asignadas a tu cargo actual.
    - Al presionar sobre el título “Objetivos de Mi Puesto”, te redirige al mismo historial detallado de seguimiento y filtros explicados arriba.
    """


@tool
def manual_dashboard_empleado_asistencia_y_evaluaciones(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando un empleado pregunte sobre su barra de progreso mensual de asistencia, 
    el recordatorio dinámico para fichar, cómo ver su historial de presentismo o dónde consultar su 
    calificación promedio anual y comentarios de evaluaciones de desempeño.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual == "normal":
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DEL DASHBOARD EMPLEADO: ASISTENCIA Y RENDIMIENTO ---
    
    1. SEGUIMIENTO DE ASISTENCIA VISUAL:
    - Vista en Dashboard: Presenta una barra de progreso mensual de tus asistencias y un recordatorio dinámico que te avisa en tiempo real si debes marcar tu "Entrada" o "Salida" según la hora del día.
    - Informe Detallado: Al presionar el título “Asistencia”, se abre tu historial completo (de más reciente a antiguo) con: Fecha, Hora de Entrada/Salida exactas, Indicador de Tardanza y si la marca fue Confirmada por tu superior.

    2. EVALUACIONES DE DESEMPEÑO:
    - Vista en Dashboard: Muestra de forma directa tu Calificación Promedio Anual y un listado con las Evaluaciones Pendientes que tienes por realizar.
    - Historial de Evaluaciones: Al ingresar, accedes al registro de tus notas pasadas detallando: Descripción del examen, Fecha de registro, Calificación Final numérica y los Comentarios u Observaciones específicas de corrección asentadas por tu evaluador.
    """


@tool
def manual_dashboard_empleado_capacitaciones_beneficios_logros(config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Úsala EXCLUSIVAMENTE cuando un empleado pregunte sobre cómo administrar su plan de formación desde el inicio, 
    las etiquetas de 'Inscripto' o el botón 'Ir al curso', cómo ver sus beneficios actuales y futuros, o cómo 
    funciona el sistema de logros, medallas e iconos iluminados.
    """
    configurable = config.get("configurable", {}) if config else {}
    rol_actual = str(configurable.get("rol_actual", "normal")).strip().lower()
    
    if rol_actual == "normal":
        return MENSAJE_PROHIBIDO
        
    return """
    --- MANUAL DEL DASHBOARD EMPLEADO: CAPACITACIONES, BENEFICIOS Y LOGROS ---
    
    1. MIS CAPACITACIONES PERSONALES:
    - Vista en Dashboard: Muestra el resumen de tus cursos activos. Las formaciones internas confirmadas muestran la etiqueta "Inscripto". Las externas muestran el botón "Ir al curso" (te redirige a la web externa correspondiente).
    - Informe Detallado (Al presionar el título “Mis Capacitaciones”): Historial con Título, Tipo (Interna/Externa), Inicio/Ritmo (fecha fija o "A tu propio ritmo"), Fecha de Inscripción, Estado (Interesado, Inscripto, Completado), Fecha de Finalización y el botón "Ir" para plataformas externas.

    2. BENEFICIOS DEL EMPLEADO:
    - Beneficios Actuales: Tarjeta con el listado de adicionales y premios que percibes hoy, detallando el Nombre del concepto y su Monto.
    - Próximos Beneficios: Sección informativa que te muestra a qué incentivos podrás acceder en el futuro si cumples determinados logros u objetivos de la empresa.

    3. SISTEMA DE LOGROS (GAMIFICACIÓN):
    - Panel de Logros: Lista el Nombre y Descripción de cada hito para que conozcas los requisitos necesarios para ganarlo (ej: "Cero Inasistencias").
    - Estados y Medallas: Cada registro indica si está "Pendiente" o "Adquirido". Al ganar un logro, su medalla/icono correspondiente se iluminará en la pantalla destacando tu avance profesional.
    """


HR_MANUAL_TOOLS = [
    manual_modulo_autenticacion_y_navegacion,    
    manual_admin_personas,
    manual_admin_cargos,
    manual_admin_departamentos,
    manual_admin_instituciones,
    manual_admin_administrar_postulaciones,
    manual_admin_gestionar_solicitudes_cargo,
    manual_admin_administrar_nominas,
    manual_admin_tipos_contrato,
    manual_admin_contratos,
    manual_admin_beneficios,
    manual_admin_descuentos,
    manual_admin_asignador_beneficios_descuentos,
    manual_admin_capacitaciones_y_cursos, 
    manual_admin_administrar_evaluaciones, 
    manual_admin_tipos_criterios,          
    manual_admin_criterios_evaluacion,  
    manual_admin_gestor_objetivos,
    manual_admin_logros,          
    manual_admin_habilidades,
    manual_operaciones_confirmar_asistencia,
    manual_operaciones_gestionar_vacaciones,
    manual_autogestion_mis_asistencias, 
    manual_autogestion_mis_nominas, 
    manual_autogestion_mis_contratos,
    manual_autogestion_mis_vacaciones,
    manual_autogestion_cursos_capacitaciones,
    manual_autogestion_ofertas_empleo,
    manual_autogestion_solicitar_personal,   
    manual_dashboard_general_ia,  
    manual_dashboard_detalle_empleados,
    manual_dashboard_detalle_asistencias,  
    manual_dashboard_detalle_costos, 
    manual_dashboard_detalle_evaluaciones,  
    manual_dashboard_graficos_vacaciones,
    manual_dashboard_graficos_asistencia,  
    manual_dashboard_graficos_costos,   
    manual_dashboard_graficos_desempenio_y_estructura, 
    manual_dashboard_graficos_objetivos_y_capacitaciones,
    manual_plataforma_chatbot_rrhh, 
    manual_dashboard_empleado_tareas_y_objetivos,            
    manual_dashboard_empleado_asistencia_y_evaluaciones,  
    manual_dashboard_empleado_capacitaciones_beneficios_logros 
]




COMBINED_HR_TOOLS = HR_TOOLS + HR_MANUAL_TOOLS