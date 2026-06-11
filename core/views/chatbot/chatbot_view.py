from datetime import date
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
from langchain_core.messages import HumanMessage
from .hr_agent import hr_agent, AnyMessage
from ...models import HistorialAsistencia 
from django_ratelimit.decorators import ratelimit 



@ratelimit(key='ip', rate='15/m', block=True, group='chatbot')
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
        return JsonResponse({
            "response": "¡Hola! Soy tu asistente de RRHH. ¿En qué te puedo ayudar hoy? 😊",
            "attendance_status": _get_attendance_status(user_id)
        }, status=200)

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
        rol_sesion = request.session.get('rol_actual')
        if not rol_sesion:
            rol_sesion = getattr(request.user, 'rol', 'normal')

        config = {
            "configurable": {
                "thread_id": f"hr_chat_{user_id}",
                "user_id": int(user_id),
                "rol_actual": str(rol_sesion) 
            }
        }
        
        input_data = {
            "messages": [HumanMessage(content=user_message_text)]
        }

        final_state = hr_agent.invoke(input_data, config=config)            
        response_text = final_state['messages'][-1].content
        
    except Exception as e:
        import traceback
        print("--- ERROR CRÍTICO EN AGENTE IA ---")
        traceback.print_exc() 
        print("---------------------------------")
        response_text = "Lo siento, experimenté una dificultad interna al procesar tu solicitud."

    return JsonResponse({
        "response": response_text,
        "attendance_status": _get_attendance_status(user_id)
    })




@ratelimit(key='ip', rate='10/m', block=True, group='chatbot')
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
