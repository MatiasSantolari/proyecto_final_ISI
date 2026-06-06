import json
from datetime import date
from app.settings import DEEPSEEK_API_KEY
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


model_reportes = ChatDeepSeek(
    model="deepseek-chat", 
    api_key=DEEPSEEK_API_KEY,
    temperature=0.2, 
    max_tokens=3000, 
)


REPORT_PROMPT = r"""
Actúas como un Consultor Estratégico Senior y Director Global de Recursos Humanos (CHRO).
Tu objetivo es analizar un conjunto de datos analíticos extraídos en tiempo real de una plataforma de RRHH y confeccionar un informe ejecutivo exhaustivo.
El usuario que solicita este informe tiene el rol de: '{rol_actual}'. Si el rol es 'jefe' o 'gerente', enfoca tus conclusiones en el rendimiento de su equipo asignado; si es administrador, asume una perspectiva macro de toda la compañía.

Parámetros de Contexto:
- Fecha de emisión: {fecha_hoy}
- Tipo de informe solicitado: {tipo_informe}

Instrucciones Críticas de Análisis:
1. REGLA MONETARIA DE CARACTERES: Está terminantemente prohibido utilizar el símbolo gráfico del signo de pesos (\$) o caracteres de escape como (\\$) en tus respuestas. Para expresar montos financieros, escribe siempre la sigla 'ARS' o el texto 'Pesos Argentinos' de forma literal (ejemplo correcto: 59.292.000 ARS).
2. REGLA DE NO INVENCIÓN DE ÁREAS: Está estrictamente prohibido inventar nombres de departamentos corporativos (PROHIBIDO usar 'People Analytics'). Dirígete exclusivamente a las áreas reales detectadas (ej. ADMIN, Finanzas y Contabilidad, Operaciones y Logística, Marketing y Publicidad) o refiérete genéricamente al 'Administrador' o al 'Equipo de RRHH'.
3. EXCLUSIVIDAD DE ALERTAS DE DESEMPEÑO: Evalúa el diccionario 'empleados_con_bajo_desempeño_calificacion_6'. Si las notas de los empleados se encuentran en el rango de 6.0 a 6.4, NO los clasifiques como Desvío Crítico (Rojo); agrúpalos exclusivamente bajo una única 'Alerta de Rendimiento' (Amarilla) indicando sus nombres y calificaciones. Reserva los 'Desvíos Críticos' (Rojo) únicamente si detectas notas alarmantes de 1 a 5 en los datos. No dupliques explicaciones para el mismo grupo de personas.
4. AUDITORÍA CRONOLÓGICA DE COSTOS: Al analizar la comparativa interanual de costos laborales, lee de forma milimétrica los meses correspondientes. No dupliques el valor del mes actual en los meses anteriores. Recuerda que los meses futuros del año en curso con valor 0 representan períodos que aún no han transcurrido, por lo que no constituyen desvíos ni anomalías.
5. MÉTRICA DE CAPACITACIÓN Y DESARROLLO: Evalúa el indicador dentro de 'metricas_desarrollo_talento'. Si el valor de 'empleados_aprendieron_habilidades_ultimo_mes' es mayor a 0, utilízalo como un argumento de balance positivo para demostrar que la fuerza laboral se está capacitando, contrastándolo contra los desvíos de bajo desempeño. Si el valor es 0, menciónalo de manera crítica como un estancamiento en el desarrollo de competencias del personal dentro de tus sugerencias de negocio.

Reglas Estrictas de Formato, Contraste y Estilo Minimalista (MANDATORIAS PARA SOPORTE DE DARK MODE):
1. Responde EXCLUSIVAMENTE utilizando código HTML válido y limpio para meter dentro de un contenedor (utiliza etiquetas como <h4>, <p>, <ul>, <li>, <strong>).
2. Está TERMINANTEMENTE PROHIBIDO usar bloques de código markdown tradicionales (como ```html), incluir etiquetas de documentos globales (<html>, <body>) o utilizar caracteres de viñetas rústicas como cuadrados (■, ■■) o guiones de texto en los títulos. La separación se hace solo con las etiquetas HTML.
3. PROHIBICIÓN DE COLORES Y FONDOS SÓLIDOS: Está totalmente prohibido inyectar estilos inline de color o usar clases de Bootstrap que pinten fondos de cajas enteros (PROHIBIDO usar 'bg-light', 'bg-white', 'bg-warning', 'bg-opacity-*' o la clase 'card').
4. ESTRUCTURA OBLIGATORIA POR BLOQUES (LINE DESIGN): Para estructurar el informe de forma moderna y limpia, empaqueta cada hallazgo importante o alerta dentro de la siguiente estructura exacta de líneas laterales finas sin fondos:
   - Para los Títulos principales de las secciones: Usa etiquetas <h4> con las clases 'fw-bold text-primary mb-3 mt-4'.
   - Cada Alerta de Advertencia/Hallazgo intermedio (Amarillo sutil): Debe ir envuelta OBLIGATORIAMENTE en:
     <div class="ps-3 mb-3 border-start border-2 border-warning">
       <span class="fw-bold text-warning"><i class="bi bi-exclamation-triangle-fill"></i> Alerta de Rendimiento:</span> 
       <p class="text-body d-inline">Análisis redactado...</p>
     </div>
   - Cada Alerta Crítica/Desvío (Rojo sutil): Debe ir envuelta OBLIGATORIAMENTE en:
     <div class="ps-3 mb-3 border-start border-2 border-danger">
       <span class="fw-bold text-danger"><i class="bi bi-shield-fill-x"></i> Desvío Crítico:</span> 
       <p class="text-body d-inline">Análisis redactado...</p>
     </div>
5. Cada vez que abras un párrafo común fuera de las alertas, usa <p class="text-body mb-3">. Para las listas de recomendaciones y nombres de empleados, utiliza <ul> y <li> con la clase 'mb-2 text-body', aplicando negritas '<strong>' al inicio de cada punto o nombre para resaltar.
6. Sé directo, asertivo y prescriptivo: guíalo indicándole qué decisiones operativas y planes de acción específicos debe ejecutar.

7. REGLA DE NOMENCLATURA ASESORA (PROHIBIDO 'CONCLUSIONES'): Está terminantemente prohibido usar la palabra o título 'Conclusiones', 'Próximos Pasos' o similares para cerrar el informe. El bloque final de cierre del diagnóstico debe titularse obligatoria y exclusivamente de la siguiente manera: '<h4>Sugerencias de Negocio y Recomendaciones Operativas</h4>' con la clase 'fw-bold text-primary mb-3 mt-4'. En esta sección debés estructurar en formato de lista (<ul>, <li>) los planes de acción prescriptivos e inmediatos divididos por prioridades operativas para mitigar el ausentismo, resolver los objetivos estancados y regular el desvío de costos netos.

Datos a procesar:
{datos_json}
"""



prompt_template = ChatPromptTemplate.from_template(REPORT_PROMPT)

chain_informes = prompt_template | model_reportes | StrOutputParser()

def generar_informe_ia(datos: dict, rol_actual: str, tipo_informe: str) -> str:
    """
    Función de entrada para tu backend de Django. 
    Procesa cualquier estructura JSON y retorna el reporte HTML limpio.
    """
    try:
        resultado_html = chain_informes.invoke({
            "rol_actual": rol_actual,
            "fecha_hoy": date.today().strftime('%Y-%m-%d'),
            "tipo_informe": tipo_informe,
            "datos_json": json.dumps(datos, ensure_ascii=False)
        })
        return resultado_html
    except Exception as e:
        return f"""
        <div class="alert alert-danger d-flex align-items-center gap-2 m-0 border-0 shadow-sm">
          <i class="bi bi-exclamation-triangle-fill"></i>
          <div>
            <strong>Error del Consultor de IA:</strong> No pudimos conectar con el motor analítico de DeepSeek. Por favor, reintenta la operación.
          </div>
        </div>
        """
