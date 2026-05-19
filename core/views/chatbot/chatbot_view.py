from datetime import date
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from langchain_core.messages import HumanMessage
from .hr_agent import hr_agent, AnyMessage
from ...models import HistorialAsistencia 

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
    get_attendance_summary_tool,
    get_recommended_courses_tool,
    get_boss_and_manager_info_tool,
    get_team_members_tool
)


@csrf_exempt
@login_required 
def get_response_chatbot(request):
    if request.method != "POST":
        return JsonResponse({"response": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    user_message_text = (data.get("message") or "").strip()
    user_id = request.user.pk
    
    if not user_message_text:
        return JsonResponse({"error": "No message provided"}, status=400)

    text_lower = user_message_text.lower()

    if "sincronizar estado de asistencia" in text_lower:
        return JsonResponse({
            "response": "", 
            "attendance_status": _get_attendance_status(user_id)
        })
    
    if "no, cancelar" in text_lower:
        return JsonResponse({
            "response": "Operación cancelada de forma segura. No se ha registrado ninguna marca en tu legajo. ¿En qué más te puedo ayudar? 😊",
            "attendance_status": _get_attendance_status(user_id)
        })


    if "sí, registrar entrada" in text_lower:
        user_message_text = "EJECUTAR_MARCA_REGISTRO_ENTRADA_CONFIRMADO"
        
    elif "sí, registrar salida" in text_lower:
        user_message_text = "EJECUTAR_MARCA_REGISTRO_SALIDA_CONFIRMADO"


    try:
        config = {
            "configurable": {
                "thread_id": f"hr_chat_{user_id}",
                "user_id": int(user_id)
            }
        }
        
        input_data = {
            "messages": [HumanMessage(content=user_message_text)]
        }

        final_state = hr_agent.invoke(input_data, config=config)            
        response_text = final_state['messages'][-1].content
        
    except Exception as e:
        print(f"Error crítico en agente de IA: {e}")
        response_text = "Lo siento, experimenté una dificultad interna al procesar tu solicitud."

    return JsonResponse({
        "response": response_text,
        "attendance_status": _get_attendance_status(user_id)
    })


def _get_attendance_status(user_id):
    """Evalúa el estado actual de las marcas del día del empleado en la Base de Datos."""
    try:
        hoy = date.today()
        
        asistencia = HistorialAsistencia.objects.filter(
            empleado__usuario=user_id, 
            fecha_asistencia=hoy
        ).first()
        
        if not asistencia:
            return "NO_ENTRY"
            
        if asistencia.hora_entrada and not asistencia.hora_salida:
            return "HAS_ENTRY" 
            
        return "COMPLETED"
    except Exception as e:
        print(f"Error de sincronización de marcas en ORM: {e}")
        return "NO_ENTRY"


@csrf_exempt
@login_required
def save_chatbot_feedback(request):
    """Recibe y audita las calificaciones (👍/👎) enviadas por los empleados."""
    if request.method != "POST":
        return JsonResponse({"status": "Método no permitido"}, status=405)
        
    try:
        data = json.loads(request.body)
        message_user = data.get("message_user", "").strip()
        message_bot = data.get("message_bot", "").strip()
        feedback_type = data.get("feedback_type", "") 
        
        print(f"--- FEEDBACK IA RECIBIDO [{feedback_type.upper()}] ---")
        print(f"Usuario Autenticado: {request.user.username}")
        print(f"Consulta Empleado: {message_user}")
        print(f"Respuesta DeepSeek: {message_bot}")
        print("-----------------------------------------")
        
        return JsonResponse({"status": "success", "message": "Feedback registrado correctamente."})
        
    except Exception as e:
        print(f"Error procesando feedback de la IA: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
