from datetime import date, timedelta, datetime
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from django.db.models import Sum, Q
from ...models import *


class GenericUserIDInput(BaseModel):
    """Input simple que requiere solo el user_id para realizar una consulta."""
    user_id: int = Field(description="El ID del usuario autenticado actual.")


@tool("get_vacation_days", args_schema=GenericUserIDInput)
def get_vacation_days_tool(user_id: int) -> str: 
    """Calcula y devuelve los días de vacaciones disponibles, usados y pendientes del empleado logueado."""
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


@tool("get_benefits", args_schema=GenericUserIDInput)
def get_benefits_tool(user_id: int) -> str:
    """Busca y lista los beneficios actuales del empleado asociado al user_id."""
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    beneficios = BeneficioEmpleadoNomina.objects.filter(empleado=empleado).order_by('-nomina__fecha_pago')[:10]
    if not beneficios.exists(): 
        return "info: el_empleado_no_tiene_beneficios_asignados"

    lista_benef = []
    for b in beneficios:
        valor = f"${b.beneficio.monto}" if b.beneficio.monto else (f"{b.beneficio.porcentaje}%" if b.beneficio.porcentaje else "activo")
        lista_benef.append(f"[{b.beneficio.descripcion}: {valor}]")
        
    return "beneficios_actuales: " + " , ".join(lista_benef)


@tool("get_discounts", args_schema=GenericUserIDInput)
def get_discounts_tool(user_id: int) -> str:
    """Busca y lista los descuentos/retenciones recientes del empleado."""
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    descuentos = DescuentoEmpleadoNomina.objects.filter(empleado=empleado).order_by('-nomina__fecha_pago')[:10]
    if not descuentos.exists(): 
        return "info: sin_descuentos_o_retenciones_registradas"
        
    lista_desc = []
    for d in descuentos:
        valor = f"${d.descuento.monto}" if d.descuento.monto else (f"{d.descuento.porcentaje}%" if d.descuento.porcentaje else "aplicado")
        lista_desc.append(f"[{d.descuento.descripcion}: {valor}]")
        
    return "descuentos_recientes: " + " , ".join(lista_desc)


@tool("get_current_role_and_department", args_schema=GenericUserIDInput)
def get_current_role_and_department_tool(user_id: int) -> str:
    """Obtiene el cargo y departamento actual del empleado."""
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    cargo_actual = EmpleadoCargo.objects.filter(empleado=empleado, fecha_fin__isnull=True).select_related('cargo').first()
    if not cargo_actual:
        return "info: sin_cargo_o_departamento_activo_en_sistema"
        
    relacion = CargoDepartamento.objects.filter(cargo=cargo_actual.cargo).select_related('departamento').first()
    depto = relacion.departamento.nombre if relacion else "No asignado"
    
    return f"cargo_actual: {cargo_actual.cargo.nombre}, departamento: {depto}"


@tool("get_employee_objectives", args_schema=GenericUserIDInput)
def get_employee_objectives_tool(user_id: int) -> str:
    """Busca y lista los objetivos actuales y completados del empleado."""
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    objetivos_activos = ObjetivoEmpleado.objects.filter(empleado=empleado, completado=False).select_related('objetivo').order_by('fecha_limite')
    objetivos_completados = ObjetivoEmpleado.objects.filter(empleado=empleado, completado=True).select_related('objetivo').order_by('-fecha_asignacion')[:5]

    if not objetivos_activos.exists() and not objetivos_completados.exists():
        return "info: el_empleado_no_tiene_objetivos_asignados"

    activos_list = [f"[{oe.objetivo.titulo} (Limite: {oe.fecha_limite.strftime('%d/%m/%Y') if oe.fecha_limite else 'Sin limite'})]" for oe in objetivos_activos]
    completados_list = [f"[{oe.objetivo.titulo}]" for oe in objetivos_completados]

    return f"objetivos_activos: {', '.join(activos_list) or 'Ninguno'}, objetivos_completados_recientes: {', '.join(completados_list) or 'Ninguno'}"


@tool("get_last_payroll", args_schema=GenericUserIDInput)
def get_last_payroll_tool(user_id: int) -> str:
    """Busca y devuelve los detalles de la última nómina (recibo de sueldo) del empleado, incluyendo montos netos, brutos, beneficios y descuentos."""
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    last_payroll = Nomina.objects.filter(empleado=empleado).order_by('-fecha_pago').first()
    if not last_payroll:
        return "info: sin_registros_de_nominas_anteriores"

    f_pago = last_payroll.fecha_pago.strftime("%d/%m/%Y") if last_payroll.fecha_pago else "N/A"
    
    return (
        f"periodo_numero: {last_payroll.numero or 'N/A'}, fecha_pago: {f_pago}, "
        f"monto_bruto: {last_payroll.monto_bruto}, total_beneficios: {last_payroll.total_beneficios}, "
        f"total_descuentos: {last_payroll.total_descuentos}, monto_neto_a_cobrar: {last_payroll.monto_neto}"
    )


@tool("get_last_performance_review", args_schema=GenericUserIDInput)
def get_last_performance_review_tool(user_id: int) -> str:
    """Busca y devuelve los detalles de la última evaluación de desempeño del empleado, incluyendo la calificación final y los criterios evaluados."""
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    last_review_emp = EvaluacionEmpleado.objects.filter(empleado=empleado).order_by('-fecha_registro').first()
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


@tool("get_current_contract_info", args_schema=GenericUserIDInput)
def get_current_contract_info_tool(user_id: int) -> str:
    """Busca y devuelve los detalles del contrato actual del empleado logueado."""
    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: return "error: empleado_no_encontrado"

    current_contract = HistorialContrato.objects.filter(empleado=empleado, estado='active').select_related('contrato', 'cargo').first()
    if not current_contract:
        current_contract = HistorialContrato.objects.filter(empleado=empleado).order_by('-fecha_inicio').first()
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


@tool("get_internal_job_applications", args_schema=GenericUserIDInput)
def get_internal_job_applications_tool(user_id: int) -> str:
    """Busca y devuelve el estado de todas las solicitudes internas de trabajo (postulaciones a cargos) que el empleado ha realizado."""
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


@tool("get_attendance_summary", args_schema=GenericUserIDInput)
def get_attendance_summary_tool(user_id: int) -> str:
    """Proporciona un resumen numérico de asistencias de los últimos 30 días, incluyendo días presentes, tardanzas y horas totales."""
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


@tool("get_recommended_courses", args_schema=GenericUserIDInput)
def get_recommended_courses_tool(user_id: int) -> str:
    """Analiza el cargo actual del empleado y devuelve los cursos de la cartelera disponibles para recomendación de la IA."""
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

    # Le pasamos las directrices de razonamiento a DeepSeek estructuradas
    return (
        f"perfil_empleado: [Cargo: '{cargo_nombre}', Departamento: '{depto_nombre}']. "
        f"cursos_disponibles_en_cartelera:\n{lista_texto}\n"
        f"INSTRUCCION: Selecciona los 2 o 3 cursos mas afines a su perfil y explica por qué le servirán."
    )


@tool("get_boss_and_manager_info", args_schema=GenericUserIDInput)
def get_boss_and_manager_info_tool(user_id: int) -> str:
    """Obtiene el nombre y mail del Jefe y del Gerente del departamento del usuario."""
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



@tool("get_team_members", args_schema=GenericUserIDInput)
def get_team_members_tool(user_id: int) -> str:
    """Obtiene la lista de compañeros de equipo (mismo departamento) y sus correos."""
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



@tool("get_available_jobs_and_referrals", args_schema=GenericUserIDInput)
def get_available_jobs_and_referrals_tool(user_id: int) -> str:
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


@tool("get_employee_achievements", args_schema=GenericUserIDInput)
def get_employee_achievements_tool(user_id: int) -> str:
    """Obtiene los logros, medallas o reconocimientos asignados al empleado y verifica si poseen beneficios corporativos cruzados."""
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
            
        achievements_list.append(
            f"[Logro: {logro_obj.get_tipo_display()} - Descripción: {logro_obj.descripcion}, Fecha_Obtencion: {fecha_logro}, {beneficio_info}]"
        )
        
    return "logros_y_medallas_del_colaborador: " + " ; ".join(achievements_list)


@tool("get_salary_evolution", args_schema=GenericUserIDInput)
def get_salary_evolution_tool(user_id: int) -> str:
    """Obtiene el historial cronológico de actualizaciones salariales base ligadas al cargo actual del empleado."""
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


###########################################


class RequestVacationInput(BaseModel):
    user_id: int = Field(description="El ID del usuario autenticado actual.")
    fecha_inicio: str = Field(description="La fecha de inicio de las vacaciones en formato YYYY-MM-DD.")
    fecha_fin: str = Field(description="La fecha de fin de las vacaciones en formato YYYY-MM-DD.")

class ApplyToJobInput(BaseModel):
    user_id: int = Field(description="El ID del usuario autenticado actual.")
    puesto_nombre: str = Field(description="El nombre exacto o aproximado del cargo vacante al que se desea postular.")



@tool("request_vacation_days", args_schema=RequestVacationInput)
def request_vacation_days_tool(user_id: int, fecha_inicio: str, fecha_fin: str) -> str:
    """Registra una nueva solicitud de vacaciones en el sistema en estado pendiente."""
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
def postulate_to_internal_job_tool(user_id: int, puesto_nombre: str) -> str:
    """Crea una postulación interna para el empleado autenticado hacia un cargo con vacantes activas en un departamento."""
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




@tool("get_training_status_and_obligations", args_schema=GenericUserIDInput)
def get_training_status_and_obligations_tool(user_id: int) -> str:
    """Busca el listado y estado de todas las capacitaciones y cursos en los que el empleado está inscripto, cursa o completó."""
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



@tool("register_daily_attendance", args_schema=GenericUserIDInput)
def register_daily_attendance_tool(user_id: int) -> str:
    """Registra la marca en tiempo real de asistencia para el día de hoy, creando la entrada o actualizando la salida según corresponda."""
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




@tool("get_employee_skills", args_schema=GenericUserIDInput)
def get_employee_skills_tool(user_id: int) -> str:
    """Busca y lista todas las habilidades y competencias técnicas asignadas al perfil del empleado, incluyendo descripciones y fechas de asignación."""
    from core.models import HabilidadEmpleado 

    empleado = Empleado.objects.filter(usuario=user_id).first()
    if not empleado: 
        return "error: empleado_no_encontrado"

    habilidades = HabilidadEmpleado.objects.filter(empleado=empleado).select_related('habilidad').order_by('-fecha_asignacion')
    
    if not habilidades.exists(): 
        return "info: el_empleado_no_tiene_habilidades_o_competencias_tecnicas_asignadas"
        
    lista_hab = []
    for h in habilidades:
        fecha_str = h.fecha_asignacion.strftime("%d/%m/%Y") if h.fecha_asignacion else "Sin fecha"
        desc = f" ({h.habilidad.descripcion})" if h.habilidad.descripcion else ""
        lista_hab.append(f"[{h.habilidad.nombre}{desc}, Asignada_El: {fecha_str}]")
        
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
