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
    get_employee_objectives_tool
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
        "hola", "buenas", "buenos dias", "que tal", "que onda", "hey", "buenos dias", "q onda", "q tal", "holis", 
        "hi", "hello", "como va", "que hay", "saludos", "q paso", "que paso", "buen dia", "buena", "que onda pa", 
        "che", "che que tal", "che hola", "ayuda", "necesito ayuda", "asistente", "bot", "rhrr", "rrhh bot"
    ]
    
    saludos_salida = [
        "chau", "bye", "hasta luego", "nos vemos", "adios", "gracias", "muchas gracias", "gracias totales", 
        "saludos", "chao", "cya", "hasta pronto", "me voy", "terminamos", "listo gracias", "eso es todo", 
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
        "que me dan", "que tengo", "que recibo", "plan de salud", "cobertura", "beneficio medico", "beneficio salud", 
        "gimnasio", "descuento gimnasio", "capacitacion", "capacitaciones", "cursos", "estudio", "estudios", "bono", "bonos",
        "plus", "premios", "aguinaldo", "obra social familiar", "afiliados", "familiares", "beneficios extras", "ticket canasta",
        "comida", "beneficio comida", "transporte", "ayuda transporte", "guarderia", "cheque guarderia", "descuento gimnasio", 
        "cuanto es el bono", "que beneficios tengo", "ver beneficios", "mis beneficios", "beneficios obra social", "plan salud"
    ]
    
    kw_descuentos = [
        "descuento", "descuentos", "retencion", "retenciones", "deduccion", "deducciones", "nomina", "sueldo", "salario", 
        "pago", "cobro", "me descuentan", "cuanto cobro", "recibo de sueldo", "recibo", "impuesto", "impuestos", "aportes", 
        "jubilacion", "afip", "sindicato", "cuota sindicato", "obra social descuento", "cuanto gano", "neto", "bruto", "sueldo neto",
        "sueldo bruto", "ver sueldo", "ver pago", "cuando pagan", "fecha de pago", "transferencia sueldo", "aumento", "aumentos",
        "paritarias", "escalafon", "categoria", "impuesto a las ganancias", "ganancias", "ingresos brutos", "retencion ganancia"
    ]
    
    kw_rol_depto = [
        "cargo", "puesto", "departamento", "depto", "mi puesto", "mi cargo", "en que area estoy", "mi area", 
        "mi departamento", "soy de", "trabajo en", "jefe", "supervisor", "gerente", "coordinador", "puesto actual", 
        "mi rol", "posicion", "categoría", "escalafon", "seniority", "fecha ingreso", "cuando entre", "antiguedad",
        "quien es mi jefe", "jefatura", "reportar a", "a quien reporto", "estructura", "organigrama", "donde trabajo", 
        "equipo", "sector", "division", "gerencia", "gerente de", "director", "directora", "mi jefe directo", "quien manda"
    ]

    kw_objetivos = [
        "objetivo", "objetivos", "metas", "meta", "performance", "rendimiento", "evaluacion", "evaluar", 
        "review", "mis objetivos", "mis metas", "que tengo que hacer", "tareas", "tarea", "asignacion", 
        "asignaciones", "objetivo anual", "objetivos del mes", "que se espera de mi", "completado", 
        "pendiente", "estado objetivos", "mis tareas", "que tengo asignado"
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

    if not response_text:
        response_text = "Lo siento, no entendí tu consulta. Por favor, sé mas específico con palabras clave."

    return JsonResponse({"response": response_text or "No tengo información sobre ese tema específico."})



## Esto se implementaria para utilizar el modo agente (problema, hay que pagar la API jiji)
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