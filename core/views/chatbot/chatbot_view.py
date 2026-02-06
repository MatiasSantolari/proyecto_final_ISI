from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from .hr_agent import hr_agent, AnyMessage, HumanMessage
from .hr_tools import (
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
)


@csrf_exempt
@login_required 
def get_response_chatbot(request):
    if request.method != "POST":
        return JsonResponse({"response": "Método no permitido"}, status=405)

    data = json.loads(request.body)

    user_message_text = (data.get("message") or "").strip()
    user = request.user 
    
    if not user_message_text:
        return JsonResponse({"error": "No message provided"}, status=400)

    text = user_message_text.lower()
    response_text = "" 

    user_id = user.pk

    saludos_entrada = [
        "hola", "buenas", "buenos dias", "que tal", "que onda", "hey", "q onda", "q tal", "holis", 
        "hi", "hello", "como va", "que hay", "saludos", "q paso", "que paso", "buen dia", "buena", "que onda pa", 
        "che", "che que tal", "che hola", "ayuda", "necesito ayuda", "asistente", "bot", "rhrr", "rrhh bot",
        "ayuda"
    ]
    
    saludos_salida = [
        "chau", "bye", "hasta luego", "nos vemos", "adios", "gracias", "muchas gracias", "gracias totales", 
        "chao", "cya", "hasta pronto", "me voy", "terminamos", "listo gracias", "eso es todo", 
        "gracias por la ayuda", "ok gracias", "gracias chau", "thanks", "thank you", "gracias mil"
    ]
    
    kw_vacaciones = [
        "vacacion", "vacaciones", "dias libres", "dia libre", "dias de vacaciones", "dia de vacaciones", 
        "dias para viajar", "dia para viajar", "pedir dias", "pedir dia", "cuantos dias tengo", "mis dias", 
        "cuantos dias me quedan", "franco", "francos", "descanso", "descansos", "tiempo libre", "ausencia", 
        "licencia", "licencias", "licencia anual", "dias habiles", "dias no habiles", "me puedo tomar", "cuanto tengo", 
        "saldo vacaciones", "consultar dias", "disponibles", "pedir vacaciones", "solicitar vacaciones", 
        "planificar vacaciones", "viajar", "viaje", "descansar", "feriado", "feriados", "dias feriados",
        "cuantos francos", "tomarse dias", "cuota vacaciones", "ver dias", "estado dias", "dias pagados", "vacaciones pagas"
    ]
    
    kw_beneficios = [
        "beneficio", "beneficios", "obra social", "obra", "social", "salud", "prepaga", "prepagada", "medicina prepaga", 
        "que me dan", "que recibo", "plan de salud", "cobertura", "beneficio medico", "beneficio salud", 
        "gimnasio", "descuento gimnasio", "capacitacion", "capacitaciones", "cursos", "estudio", "estudios", "bono", "bonos",
        "plus", "premios", "aguinaldo", "obra social familiar", "afiliados", "familiares", "beneficios extras", "ticket canasta",
        "comida", "beneficio comida", "transporte", "ayuda transporte", "guarderia", "cheque guarderia", 
        "cuanto es el bono", "que beneficios tengo", "ver beneficios", "mis beneficios", "beneficios obra social", "plan salud"
    ]
    
    kw_descuentos = [
        "descuento", "descuentos", "retencion", "retenciones", "deduccion", "deducciones", "impuesto", "impuestos", "aportes", 
        "jubilacion", "afip", "sindicato", "cuota sindicato", "retencion ganancia", 
        "impuesto a las ganancias", "ganancias", "ingresos brutos"
    ]
    
    kw_rol_depto = [
        "cargo", "puesto", "departamento", "depto", "mi puesto", "mi cargo", "en que area estoy", "mi area", 
        "mi departamento", "soy de", "trabajo en", "jefe", "supervisor", "gerente", "coordinador", "puesto actual", 
        "mi rol", "posicion", "categoría", "escalafon", "seniority", "fecha ingreso", "cuando entre", "antiguedad",
        "quien es mi jefe", "jefatura", "reportar a", "a quien reporto", "estructura", "organigrama", "donde trabajo", 
        "equipo", "sector", "division", "gerencia", "gerente de", "director", "directora", "mi jefe directo", "quien manda"
    ]

    kw_objetivos = [
        "objetivo", "objetivos", "metas", "meta", "performance", "rendimiento", "que tengo asignado",
        "review", "mis objetivos", "mis metas", "que tengo que hacer", "tareas", "tarea", "asignacion", 
        "asignaciones", "objetivo anual", "objetivos del mes", "que se espera de mi", "completado", 
        "pendiente", "estado objetivos", "mis tareas"
    ]
    
    kw_nomina = [
        "nomina", "nómina", "recibo sueldo", "recibo de sueldo", "sueldo", "salario", 
        "pago", "cobro", "monto neto", "monto bruto", "mi pago", "cuanto cobré", 
        "ver sueldo", "ultima nomina", "nomina mes", "liquidación", "liquidacion sueldo",
        "monto bruto", "monto neto", "cuanto gano", "neto", "bruto", "sueldo neto",
        "sueldo bruto", "ver sueldo", "ver pago", "cuando pagan", "fecha de pago", "transferencia sueldo"
    ]

    kw_evaluaciones = [
        "evaluacion", "evaluaciones", "evaluar", "desempeño", "rendimiento", "performance",
        "calificacion", "mis notas", "nota", "review", "puntuacion", "puntaje",
        "como me fue", "evaluacion anual", "evaluacion de desempeño", "mis evaluaciones"
    ]
    
    kw_contrato = [
        "contrato", "tipo de contrato", "mi contrato", "condiciones contrato", 
        "fecha inicio", "fecha fin", "finalizacion contrato", "estado contrato",
        "sueldo pactado", "monto extra", "activo", "renovacion", "terminar contrato",
        "vence", "cuando termina"
    ]

    kw_postulaciones = [
        "postulacion", "postulaciones", "solicitud cargo", "cargos internos", 
        "aplicacion trabajo", "trabajo interno", "busqueda interna", "moverme de puesto",
        "cambio de cargo", "estado solicitud", "mis solicitudes", "carrera", "puestos disponibles"
    ]

    kw_asistencia = [
        "asistencia", "presente", "ausente", "falta", "faltas", "llegada tarde", "horas trabajadas",
        "ingreso", "salida", "mi horario", "registro horario", "checador", "fichaje", "mis asistencias"
    ]
    

    if any(saludo in text for saludo in saludos_entrada):
        response_text = f"¡Hola {user.persona.nombre}! 👋 Soy tu asistente virtual de RRHH. ¿En qué puedo ayudarte hoy?"
    elif any(saludo in text for saludo in saludos_salida):
        response_text = f"De nada {user.persona.nombre}, ¡que tengas un excelente día! 😊"
    elif any(kw in text for kw in kw_vacaciones):
        response_text = get_vacation_days_tool.invoke({"user_id": user_id}) 
    elif any(kw in text for kw in kw_beneficios):
        response_text = get_benefits_tool.invoke({"user_id": user_id})   
    elif any(kw in text for kw in kw_descuentos):
        response_text = get_discounts_tool.invoke({"user_id": user_id})   
    elif any(kw in text for kw in kw_rol_depto):
        response_text = get_current_role_and_department_tool.invoke({"user_id": user_id}) 
    elif any(kw in text for kw in kw_objetivos):
        response_text = get_employee_objectives_tool.invoke({"user_id": user_id}) 
    elif any(kw in text for kw in kw_nomina):
        response_text = get_last_payroll_tool.invoke({"user_id": user_id})
    elif any(kw in text for kw in kw_evaluaciones):
        response_text = get_last_performance_review_tool.invoke({"user_id": user_id})
    elif any(kw in text for kw in kw_contrato):
        response_text = get_current_contract_info_tool.invoke({"user_id": user_id})
    elif any(kw in text for kw in kw_postulaciones):
        response_text = get_internal_job_applications_tool.invoke({"user_id": user_id})
    elif any(kw in text for kw in kw_asistencia):
        response_text = get_attendance_summary_tool.invoke({"user_id": user_id})
  

    if not response_text:
        response_text = "Lo siento, no entendí tu consulta. Por favor, sé mas específico con palabras clave."


    ## Esto se implementaria para utilizar el modo agente AI pro
    ## Cuando el metodo manual no puede dar una respuesta, se produce un fallback y llama al modo agente
    ## (Para activarlo hay que pagar la API, igual que creo es barata)
    ## Se reemplaza el "response_text = "Lo siento, no entendí...." por el codigo comentado de abajo
        '''
        if not response_text:        
            try:
                config = {"configurable": {"thread_id": f"hr_chat_intention_{user_id}"}}
                input_message = HumanMessage(content=text)
            
                final_state = hr_agent.invoke({"messages": [input_message]}, config=config)            
                last_message = final_state['messages'][-1]
                if last_message.type == 'ai':
                    response_text = last_message.content
                else:
                    response_text = "Hubo un problema con la respuesta de la IA. Intenta de nuevo."

            except Exception as e:
                print(f"Error executing HR Agent as fallback: {e}")
                response_text = "Lo siento, hubo un error general al procesar tu consulta."
        ''' 
    return JsonResponse({"response": response_text or "No tengo información sobre ese tema específico."})



