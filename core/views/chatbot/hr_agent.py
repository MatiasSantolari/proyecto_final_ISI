from langgraph.prebuilt import create_react_agent 
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from typing import Annotated, TypedDict, List
from .hr_tools import HR_TOOLS 

model = ChatOpenAI(
    model="gpt-5-mini",   
    temperature=0 
)
checkpointer = MemorySaver() 

class HRAgentState(TypedDict):
    messages: Annotated[List[AnyMessage], lambda x, y: x + y]

HR_PROMPT = """
Eres un asistente virtual de Recursos Humanos amable, profesional y servicial llamado 'RRHH Bot' de [Nombre de tu Empresa]. 
Tu objetivo principal es responder preguntas de los empleados sobre sus datos personales de RRHH (vacaciones, beneficios, descuentos, cargo) y preguntas generales sobre políticas de la empresa.

Instrucciones CRÍTICAS:
1. Responde siempre en **español**.
2. Utiliza un tono personal, positivo y amigable, usando emojis si es apropiado.
3. Utiliza las herramientas disponibles (get_vacation_days_tool, get_benefits_tool, get_discounts_tool, 
    get_current_role_and_department_tool, get_employee_objectives_tool, get_last_payroll_tool, get_last_performance_review, get_current_contract_info, get_internal_job_applications, get_attendance_summary_tool, etc.) SIEMPRE que el usuario pregunte por sus datos personales.
4. NO inventes información confidencial ni financiera.
5. Si el usuario saluda, responde de forma amigable.

6. **REGLA DE FALLO:** Si no puedes determinar la respuesta usando tus herramientas o tu conocimiento general, usa esta frase exacta: "Lo siento, no entendí bien a qué te refieres. ¿Podrías reformular tu pregunta o usar palabras clave como 'vacaciones', 'beneficios' o 'cargo'?"
"""

def prompt_builder(state: HRAgentState):
    system_msg = SystemMessage(content=HR_PROMPT)
    return [system_msg] + state["messages"]

hr_agent = create_react_agent(
    model,
    tools=HR_TOOLS,
    prompt=prompt_builder,
    checkpointer=checkpointer,
)