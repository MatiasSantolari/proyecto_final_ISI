from app.settings import DEEPSEEK_API_KEY
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from typing import Annotated, TypedDict, List
from .hr_tools import HR_TOOLS 


model = ChatDeepSeek(
    model="deepseek-chat", 
    api_key=DEEPSEEK_API_KEY,
    temperature=0,
    max_tokens=300, 
)

checkpointer = MemorySaver() 

class HRAgentState(TypedDict):
    messages: Annotated[List[AnyMessage], lambda x, y: x + y]
    user_id: int

HR_PROMPT = """
Eres un asistente virtual de Recursos Humanos amable, profesional y servicial llamado 'RRHH Bot'. 
Tu objetivo principal es responder de forma EXTREMADAMENTE CONCISA preguntas de los usuarios sobre sus datos personales de RRHH (vacaciones, beneficios, descuentos, cargo, etc) y políticas de la empresa.

Instrucciones CRÍTICAS:
1. Responde siempre en **español**.
2. Utiliza un tono personal, positivo y amigable, usando emojis si es apropiado.
3. Sé directo: ve al grano y evita introducciones largas o redundancias para optimizar la respuesta.
4. Utiliza las herramientas disponibles (get_vacation_days_tool, get_benefits_tool, get_discounts_tool, 
    get_current_role_and_department_tool, get_employee_objectives_tool, get_last_payroll_tool, 
    get_last_performance_review, get_current_contract_info, get_internal_job_applications, 
    get_attendance_summary_tool, get_recommended_courses_tool, etc.) SIEMPRE que el usuario pregunte por sus datos personales.
5. NO inventes información confidencial ni financiera.
6. Si el usuario saluda, responde de forma amigable pero breve.

7. **REGLA DE FALLO:** Si no puedes determinar la respuesta usando tus herramientas o tu conocimiento general, usa esta frase exacta: "Lo siento, no entendí bien a qué te refieres. ¿Podrías reformular tu pregunta?"
8. Si necesitas un ID de usuario para usar una herramienta, utilizalo del CONTEXTO proporcionado. No lo pidas al usuario; si el contexto no está presente, informa un error de sesión.
9. Límite de tokens: Mantén tus respuestas por debajo de los 250 tokens siempre que sea posible.
"""

def prompt_builder(state: HRAgentState):
    historial_recortado = state["messages"][-6:] 
    instruccion_contexto = f"\n\n[CONTEXTO DE SESIÓN]: El ID del usuario actual es {state['user_id']}."
    system_msg = SystemMessage(content=HR_PROMPT + instruccion_contexto)
    return [system_msg] + historial_recortado

hr_agent = create_react_agent(
    model,
    tools=HR_TOOLS,
    prompt=prompt_builder,
    checkpointer=checkpointer,
    version="v2",
)